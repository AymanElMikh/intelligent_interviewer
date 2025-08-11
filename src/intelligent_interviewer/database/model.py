# database/models.py
import uuid
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class BaseModel(Base):
    """Base model with common fields and functionality"""
    
    __abstract__ = True
    
    # Primary key - works with PostgreSQL, MySQL, and SQLite
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary"""
        # Filter out keys that don't exist as columns
        valid_keys = {column.name for column in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        valid_keys = {column.name for column in self.__table__.columns}
        
        for key, value in data.items():
            if key in valid_keys and hasattr(self, key):
                # Don't update id and created_at
                if key not in ('id', 'created_at'):
                    setattr(self, key, value)


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before update"""
    target.updated_at = datetime.utcnow()


@event.listens_for(BaseModel, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    """Set timestamps before insert if not already set"""
    now = datetime.utcnow()
    if target.created_at is None:
        target.created_at = now
    if target.updated_at is None:
        target.updated_at = now


# PostgreSQL-specific base model with UUID primary key
class PostgreSQLBaseModel(Base):
    """Base model optimized for PostgreSQL with UUID primary key"""
    
    __abstract__ = True
    
    # UUID primary key for PostgreSQL
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostgreSQLBaseModel":
        """Create model instance from dictionary"""
        valid_keys = {column.name for column in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        if 'id' in filtered_data and isinstance(filtered_data['id'], str):
            try:
                filtered_data['id'] = uuid.UUID(filtered_data['id'])
            except ValueError:
                pass  # Let SQLAlchemy handle the error
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        valid_keys = {column.name for column in self.__table__.columns}
        
        for key, value in data.items():
            if key in valid_keys and hasattr(self, key):
                # Don't update id and created_at
                if key not in ('id', 'created_at'):
                    # Convert string UUIDs to UUID objects
                    if key == 'id' and isinstance(value, str):
                        try:
                            value = uuid.UUID(value)
                        except ValueError:
                            continue  # Skip invalid UUIDs
                    setattr(self, key, value)


# Apply the same event listeners to PostgreSQL base model
@event.listens_for(PostgreSQLBaseModel, 'before_update', propagate=True)
def receive_before_update_pg(mapper, connection, target):
    """Update the updated_at timestamp before update"""
    target.updated_at = datetime.utcnow()


@event.listens_for(PostgreSQLBaseModel, 'before_insert', propagate=True)
def receive_before_insert_pg(mapper, connection, target):
    """Set timestamps before insert if not already set"""
    now = datetime.utcnow()
    if target.created_at is None:
        target.created_at = now
    if target.updated_at is None:
        target.updated_at = now


# Factory function to get the appropriate base model
def get_base_model(database_type: str = "generic") -> type:
    """
    Get the appropriate base model class based on database type
    
    Args:
        database_type: Type of database ('postgresql', 'mysql', 'sqlite', 'generic')
    
    Returns:
        Appropriate base model class
    """
    if database_type.lower() == "postgresql":
        return PostgreSQLBaseModel
    else:
        return BaseModel


# Utility functions for model operations
def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert any model instance to dictionary"""
    if hasattr(model, 'to_dict'):
        return model.to_dict()
    
    # Fallback for models that don't inherit from BaseModel
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, uuid.UUID):
            value = str(value)
        result[column.name] = value
    return result


def dict_to_model(model_class: type, data: Dict[str, Any]) -> BaseModel:
    """Convert dictionary to model instance"""
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    
    # Fallback for models that don't inherit from BaseModel
    valid_keys = {column.name for column in model_class.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
    return model_class(**filtered_data)


# Mixins for additional functionality
class TimestampMixin:
    """Mixin for models that need timestamp functionality without full BaseModel"""
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    def soft_delete(self):
        """Mark record as deleted"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore soft-deleted record"""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None