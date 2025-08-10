from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound
from ..database.connection import get_session
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError, NotFoundError, ValidationError

T = TypeVar('T')
U = TypeVar('U')

class BaseRepository(Generic[T, U], ABC):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model_class: type[T], db_model_class: type[U]):
        self.model_class = model_class
        self.db_model_class = db_model_class
        self.logger = get_logger(self.__class__.__name__)
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new record"""
        try:
            async with get_session() as session:
                db_obj = self.db_model_class(**data)
                session.add(db_obj)
                await session.commit()
                await session.refresh(db_obj)
                return self._to_model(db_obj)
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {str(e)}")
            raise ValidationError(f"Data validation failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to create record: {str(e)}")
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID"""
        try:
            async with get_session() as session:
                query = select(self.db_model_class).where(self.db_model_class.id == id)
                result = await session.execute(query)
                db_obj = result.scalar_one_or_none()
                return self._to_model(db_obj) if db_obj else None
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve record: {str(e)}")
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination"""
        try:
            async with get_session() as session:
                query = select(self.db_model_class).limit(limit).offset(offset)
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting all {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve records: {str(e)}")
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update record by ID"""
        try:
            async with get_session() as session:
                query = select(self.db_model_class).where(self.db_model_class.id == id)
                result = await session.execute(query)
                db_obj = result.scalar_one_or_none()
                
                if not db_obj:
                    return None
                
                for key, value in data.items():
                    if hasattr(db_obj, key):
                        setattr(db_obj, key, value)
                
                await session.commit()
                await session.refresh(db_obj)
                return self._to_model(db_obj)
        except Exception as e:
            self.logger.error(f"Error updating {self.model_class.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Failed to update record: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete record by ID"""
        try:
            async with get_session() as session:
                query = delete(self.db_model_class).where(self.db_model_class.id == id)
                result = await session.execute(query)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting {self.model_class.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete record: {str(e)}")
    
    async def exists(self, id: str) -> bool:
        """Check if record exists"""
        try:
            async with get_session() as session:
                query = select(self.db_model_class.id).where(self.db_model_class.id == id)
                result = await session.execute(query)
                return result.scalar_one_or_none() is not None
        except Exception as e:
            self.logger.error(f"Error checking existence of {self.model_class.__name__} {id}: {str(e)}")
            return False
    
    @abstractmethod
    def _to_model(self, db_obj: U) -> T:
        """Convert database model to business model"""
        pass
