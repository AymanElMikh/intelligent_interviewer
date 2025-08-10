from sqlalchemy import Column, String, Integer, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

Base = declarative_base()

class Department(str, Enum):
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"

class EmployeeLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"

# Database Model (SQLAlchemy)
class EmployeeDB(Base):
    __tablename__ = "employees"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    position = Column(String, nullable=False)
    department = Column(String, nullable=False)
    level = Column(String, nullable=False)
    experience_years = Column(Integer, default=0)
    skills = Column(JSON, default=list)  # List of skills
    performance_ratings = Column(JSON, default=list)  # Historical ratings
    manager_id = Column(String, nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)
    salary = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interviews = relationship("InterviewDB", back_populates="employee")

# Pydantic Models (API/Business Logic)
class Employee(BaseModel):
    """Main employee data model"""
    id: str
    name: str
    email: EmailStr
    position: str
    department: Department
    level: EmployeeLevel
    experience_years: int
    skills: List[str] = []
    performance_ratings: List[Dict[str, Any]] = []
    manager_id: Optional[str] = None
    hire_date: datetime
    salary: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    """Model for creating new employees"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    position: str = Field(..., min_length=2, max_length=100)
    department: Department
    level: EmployeeLevel
    experience_years: int = Field(0, ge=0, le=50)
    skills: List[str] = []
    manager_id: Optional[str] = None
    salary: Optional[float] = Field(None, gt=0)

class EmployeeProfile(BaseModel):
    """Simplified employee profile for AI agents"""
    id: str
    name: str
    position: str
    department: str
    level: str
    experience_years: int
    skills: List[str]
    recent_performance: Optional[Dict[str, Any]] = None
    career_goals: Optional[List[str]] = None