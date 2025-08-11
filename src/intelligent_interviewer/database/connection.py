# database/connection.py
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import (
    AsyncEngine, 
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.engine.events import event
from sqlalchemy import text
import time
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError, ConfigurationError

logger = get_logger(__name__)


class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        connect_args: Optional[Dict[str, Any]] = None,
        execution_options: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.connect_args = connect_args or {}
        self.execution_options = execution_options or {}
        
        # Validate URL
        if not url:
            raise ConfigurationError("Database URL is required")
        
        # Set default connect args for different databases
        if "postgresql" in url or "asyncpg" in url:
            self.connect_args.setdefault("server_settings", {
                "jit": "off",
                "application_name": "async-app"
            })
        elif "mysql" in url:
            self.connect_args.setdefault("charset", "utf8mb4")
        elif "sqlite" in url:
            self.connect_args.setdefault("check_same_thread", False)
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables"""
        import os
        
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ConfigurationError("DATABASE_URL environment variable is required")
        
        return cls(
            url=url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
            pool_pre_ping=os.getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true",
        )


class DatabaseManager:
    """Manages database engine and session lifecycle"""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._config: Optional[DatabaseConfig] = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "total_queries": 0,
        }
    
    async def initialize(self, config: DatabaseConfig) -> None:
        """Initialize the database engine and session factory"""
        if self._engine:
            logger.warning("Database already initialized, skipping...")
            return
        
        self._config = config
        
        try:
            # Determine poolclass based on database type
            if "sqlite" in config.url:
                # SQLite doesn't support connection pooling
                poolclass = NullPool
                pool_kwargs = {}
            else:
                poolclass = QueuePool
                pool_kwargs = {
                    "pool_size": config.pool_size,
                    "max_overflow": config.max_overflow,
                    "pool_timeout": config.pool_timeout,
                    "pool_recycle": config.pool_recycle,
                    "pool_pre_ping": config.pool_pre_ping,
                }
            
            # Create async engine
            self._engine = create_async_engine(
                config.url,
                echo=config.echo,
                poolclass=poolclass,
                connect_args=config.connect_args,
                execution_options=config.execution_options,
                **pool_kwargs
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Set up event listeners for monitoring
            self._setup_event_listeners()
            
            # Test connection
            await self._test_connection()
            
            logger.info("Database initialized successfully", extra={
                "database_type": self._get_database_type(),
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow
            })
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}", cause=e)
    
    async def close(self) -> None:
        """Close the database engine and all connections"""
        if self._engine:
            logger.info("Closing database connections...")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    def get_session_factory(self) -> async_sessionmaker:
        """Get the session factory"""
        if not self._session_factory:
            raise DatabaseError("Database not initialized. Call initialize() first.")
        return self._session_factory
    
    def get_engine(self) -> AsyncEngine:
        """Get the database engine"""
        if not self._engine:
            raise DatabaseError("Database not initialized. Call initialize() first.")
        return self._engine
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        if not self._engine:
            return {
                "status": "unhealthy",
                "error": "Database not initialized"
            }
        
        try:
            start_time = time.time()
            
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Get pool status if available
            pool_status = {}
            if hasattr(self._engine.pool, 'size'):
                pool_status = {
                    "pool_size": self._engine.pool.size(),
                    "checked_in": self._engine.pool.checkedin(),
                    "checked_out": self._engine.pool.checkedout(),
                    "overflow": getattr(self._engine.pool, 'overflow', lambda: 0)(),
                }
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "database_type": self._get_database_type(),
                "pool_status": pool_status,
                "connection_stats": self._connection_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_stats": self._connection_stats.copy()
            }
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            self._connection_stats["total_connections"] += 1
            self._connection_stats["active_connections"] += 1
            logger.debug("New database connection established")
        
        @event.listens_for(self._engine.sync_engine, "close")
        def on_close(dbapi_conn, connection_record):
            self._connection_stats["active_connections"] -= 1
            logger.debug("Database connection closed")
        
        @event.listens_for(self._engine.sync_engine, "handle_error")
        def on_error(exception_context):
            self._connection_stats["failed_connections"] += 1
            logger.error(f"Database connection error: {exception_context.original_exception}")
        
        @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
        def on_before_execute(conn, cursor, statement, parameters, context, executemany):
            self._connection_stats["total_queries"] += 1
            context._query_start_time = time.time()
            logger.debug(f"Executing query: {statement[:100]}...")
        
        @event.listens_for(self._engine.sync_engine, "after_cursor_execute")
        def on_after_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log slow queries (> 1 second)
                logger.warning(
                    f"Slow query detected: {total:.2f}s",
                    extra={
                        "query": statement[:200],
                        "duration": total
                    }
                )
    
    async def _test_connection(self) -> None:
        """Test database connection"""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.debug("Database connection test successful")
        except Exception as e:
            raise DatabaseError(f"Database connection test failed: {str(e)}", cause=e)
    
    def _get_database_type(self) -> str:
        """Get database type from URL"""
        if not self._config:
            return "unknown"
        
        url = self._config.url.lower()
        if "postgresql" in url or "asyncpg" in url:
            return "postgresql"
        elif "mysql" in url or "aiomysql" in url:
            return "mysql"
        elif "sqlite" in url:
            return "sqlite"
        elif "oracle" in url:
            return "oracle"
        elif "mssql" in url:
            return "mssql"
        else:
            return "unknown"


# Global database manager instance
_db_manager = DatabaseManager()


async def initialize_database(config: Optional[DatabaseConfig] = None) -> None:
    """Initialize the global database manager"""
    if config is None:
        config = DatabaseConfig.from_env()
    
    await _db_manager.initialize(config)


async def close_database() -> None:
    """Close the global database manager"""
    await _db_manager.close()


def get_engine() -> AsyncEngine:
    """Get the database engine"""
    return _db_manager.get_engine()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session
    
    Usage:
        async with get_session() as session:
            # Use session here
            result = await session.execute(query)
    """
    session_factory = _db_manager.get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error, rolling back: {str(e)}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with automatic transaction management
    
    Usage:
        async with get_transaction() as session:
            # Operations here are automatically committed
            # or rolled back on exception
    """
    async with get_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                # Transaction will be automatically rolled back
                logger.error(f"Transaction failed, rolling back: {str(e)}")
                raise


async def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    return await _db_manager.health_check()


# Context manager for database lifecycle
class DatabaseLifecycle:
    """Context manager for database lifecycle management"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config
    
    async def __aenter__(self):
        await initialize_database(self.config)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await close_database()


# Decorator for database operations
def with_database_session(func):
    """Decorator to inject database session into function"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session() as session:
            return await func(session, *args, **kwargs)
    
    return wrapper


# Example usage and testing utilities
async def test_database_connection() -> bool:
    """Test database connection and return True if successful"""
    try:
        health = await get_database_health()
        return health["status"] == "healthy"
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False