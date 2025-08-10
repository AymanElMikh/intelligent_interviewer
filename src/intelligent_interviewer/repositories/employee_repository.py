from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from datetime import datetime
from .base_repository import BaseRepository
from ..models.employee import Employee, EmployeeDB, Department, EmployeeLevel

class EmployeeRepository(BaseRepository[Employee, EmployeeDB]):
    """Repository for employee data operations"""
    
    def __init__(self):
        super().__init__(Employee, EmployeeDB)
    
    async def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email address"""
        try:
            async with get_session() as session:
                query = select(EmployeeDB).where(EmployeeDB.email == email)
                result = await session.execute(query)
                db_obj = result.scalar_one_or_none()
                return self._to_model(db_obj) if db_obj else None
        except Exception as e:
            self.logger.error(f"Error getting employee by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve employee: {str(e)}")
    
    async def get_by_department(self, department: Department) -> List[Employee]:
        """Get all employees in a department"""
        try:
            async with get_session() as session:
                query = select(EmployeeDB).where(EmployeeDB.department == department.value)
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting employees by department {department}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve employees: {str(e)}")
    
    async def get_by_manager(self, manager_id: str) -> List[Employee]:
        """Get all employees reporting to a manager"""
        try:
            async with get_session() as session:
                query = select(EmployeeDB).where(EmployeeDB.manager_id == manager_id)
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting employees by manager {manager_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve employees: {str(e)}")
    
    async def search_by_skills(self, skills: List[str]) -> List[Employee]:
        """Search employees by skills"""
        try:
            async with get_session() as session:
                # Create conditions for each skill
                skill_conditions = []
                for skill in skills:
                    skill_conditions.append(EmployeeDB.skills.contains([skill]))
                
                query = select(EmployeeDB).where(or_(*skill_conditions))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error searching employees by skills {skills}: {str(e)}")
            raise DatabaseError(f"Failed to search employees: {str(e)}")
    
    async def get_by_level_range(self, min_level: EmployeeLevel, max_level: EmployeeLevel) -> List[Employee]:
        """Get employees within a level range"""
        level_hierarchy = {
            EmployeeLevel.INTERN: 0,
            EmployeeLevel.JUNIOR: 1,
            EmployeeLevel.MID: 2,
            EmployeeLevel.SENIOR: 3,
            EmployeeLevel.LEAD: 4,
            EmployeeLevel.MANAGER: 5,
            EmployeeLevel.DIRECTOR: 6
        }
        
        min_order = level_hierarchy[min_level]
        max_order = level_hierarchy[max_level]
        
        valid_levels = [level.value for level, order in level_hierarchy.items() 
                       if min_order <= order <= max_order]
        
        try:
            async with get_session() as session:
                query = select(EmployeeDB).where(EmployeeDB.level.in_(valid_levels))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting employees by level range: {str(e)}")
            raise DatabaseError(f"Failed to retrieve employees: {str(e)}")
    
    async def add_performance_rating(self, employee_id: str, rating: Dict[str, Any]) -> bool:
        """Add a performance rating to employee's history"""
        try:
            employee = await self.get_by_id(employee_id)
            if not employee:
                return False
            
            # Add timestamp if not provided
            if 'date' not in rating:
                rating['date'] = datetime.utcnow().isoformat()
            
            # Get current ratings and append new one
            current_ratings = employee.performance_ratings or []
            current_ratings.append(rating)
            
            # Update employee
            await self.update(employee_id, {"performance_ratings": current_ratings})
            return True
        except Exception as e:
            self.logger.error(f"Error adding performance rating: {str(e)}")
            return False
    
    async def update_skills(self, employee_id: str, skills: List[str]) -> bool:
        """Update employee's skills list"""
        try:
            await self.update(employee_id, {"skills": skills})
            return True
        except Exception as e:
            self.logger.error(f"Error updating skills for employee {employee_id}: {str(e)}")
            return False
    
    async def get_team_members(self, department: Department, level: Optional[EmployeeLevel] = None) -> List[Employee]:
        """Get team members by department and optionally by level"""
        try:
            async with get_session() as session:
                conditions = [EmployeeDB.department == department.value]
                if level:
                    conditions.append(EmployeeDB.level == level.value)
                
                query = select(EmployeeDB).where(and_(*conditions))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting team members: {str(e)}")
            raise DatabaseError(f"Failed to retrieve team members: {str(e)}")
    
    def _to_model(self, db_obj: EmployeeDB) -> Employee:
        """Convert EmployeeDB to Employee model"""
        return Employee(
            id=db_obj.id,
            name=db_obj.name,
            email=db_obj.email,
            position=db_obj.position,
            department=Department(db_obj.department),
            level=EmployeeLevel(db_obj.level),
            experience_years=db_obj.experience_years,
            skills=db_obj.skills or [],
            performance_ratings=db_obj.performance_ratings or [],
            manager_id=db_obj.manager_id,
            hire_date=db_obj.hire_date,
            salary=db_obj.salary,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at
        )
