
# database/__init__.py
"""Database package initialization and convenience imports"""

from .connection import (
    DatabaseConfig,
    DatabaseManager,
    initialize_database,
    close_database,
    get_session,
    get_transaction,
    get_engine,
    get_database_health,
    DatabaseLifecycle,
    with_database_session,
    test_database_connection
)

from .models import (
    Base,
    BaseModel,
    PostgreSQLBaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    get_base_model,
    model_to_dict,
    dict_to_model
)

__all__ = [
    # Connection
    'DatabaseConfig',
    'DatabaseManager', 
    'initialize_database',
    'close_database',
    'get_session',
    'get_transaction',
    'get_engine',
    'get_database_health',
    'DatabaseLifecycle',
    'with_database_session',
    'test_database_connection',
    
    # Models
    'Base',
    'BaseModel',
    'PostgreSQLBaseModel',
    'TimestampMixin',
    'SoftDeleteMixin',
    'get_base_model',
    'model_to_dict',
    'dict_to_model'
]


# Example usage and setup functions
async def setup_database(database_url: str, **kwargs) -> None:
    """
    Quick setup function for database initialization
    
    Args:
        database_url: Database connection URL
        **kwargs: Additional configuration options
    """
    config = DatabaseConfig(url=database_url, **kwargs)
    await initialize_database(config)


# Example application startup/shutdown
class DatabaseApp:
    """Example application class with database lifecycle management"""
    
    def __init__(self, database_url: str, **db_config):
        self.database_url = database_url
        self.db_config = db_config
        
    async def startup(self):
        """Application startup - initialize database"""
        try:
            config = DatabaseConfig(url=self.database_url, **self.db_config)
            await initialize_database(config)
            
            # Test connection
            health = await get_database_health()
            if health["status"] != "healthy":
                raise Exception(f"Database unhealthy: {health}")
                
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise
    
    async def shutdown(self):
        """Application shutdown - close database"""
        try:
            await close_database()
            print("✅ Database closed successfully")
        except Exception as e:
            print(f"❌ Error closing database: {e}")


# Example environment-based configuration
def get_database_config_from_env() -> DatabaseConfig:
    """Get database configuration from environment variables"""
    import os
    
    # Required
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Optional with defaults
    return DatabaseConfig(
        url=database_url,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
    )
