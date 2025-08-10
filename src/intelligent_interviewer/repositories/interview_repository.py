from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from ..models.interview import Interview, InterviewDB, InterviewType, InterviewStatus

class InterviewRepository(BaseRepository[Interview, InterviewDB]):
    """Repository for interview data operations"""
    
    def __init__(self):
        super().__init__(Interview, InterviewDB)
    
    async def get_by_employee(self, employee_id: str) -> List[Interview]:
        """Get all interviews for an employee"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    InterviewDB.employee_id == employee_id
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting interviews for employee {employee_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def get_by_type(self, interview_type: InterviewType) -> List[Interview]:
        """Get all interviews by type"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    InterviewDB.interview_type == interview_type.value
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting interviews by type {interview_type}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def get_by_status(self, status: InterviewStatus) -> List[Interview]:
        """Get all interviews by status"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    InterviewDB.status == status.value
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting interviews by status {status}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def get_by_department(self, department: str) -> List[Interview]:
        """Get interviews by department (joins with employee table)"""
        try:
            async with get_session() as session:
                # This would require a join with the employee table
                query = select(InterviewDB).join(EmployeeDB).where(
                    EmployeeDB.department == department
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting interviews by department {department}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def get_recent(self, cutoff_date: datetime) -> List[Interview]:
        """Get recent interviews since cutoff date"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    InterviewDB.created_at >= cutoff_date
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting recent interviews: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def get_pending_interviews(self) -> List[Interview]:
        """Get all pending interviews"""
        return await self.get_by_status(InterviewStatus.SCHEDULED)
    
    async def get_completed_interviews(self, limit: int = 50) -> List[Interview]:
        """Get completed interviews"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    InterviewDB.status == InterviewStatus.COMPLETED.value
                ).order_by(desc(InterviewDB.created_at)).limit(limit)
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting completed interviews: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    async def update_status(self, interview_id: str, status: InterviewStatus) -> bool:
        """Update interview status"""
        try:
            result = await self.update(interview_id, {"status": status.value})
            return result is not None
        except Exception as e:
            self.logger.error(f"Error updating interview status: {str(e)}")
            return False
    
    async def add_responses(self, interview_id: str, responses: Dict[str, str]) -> bool:
        """Add responses to an interview"""
        try:
            result = await self.update(interview_id, {"responses": responses})
            return result is not None
        except Exception as e:
            self.logger.error(f"Error adding responses to interview: {str(e)}")
            return False
    
    async def get_interviews_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Interview]:
        """Get interviews within a date range"""
        try:
            async with get_session() as session:
                query = select(InterviewDB).where(
                    and_(
                        InterviewDB.created_at >= start_date,
                        InterviewDB.created_at <= end_date
                    )
                ).order_by(desc(InterviewDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting interviews by date range: {str(e)}")
            raise DatabaseError(f"Failed to retrieve interviews: {str(e)}")
    
    def _to_model(self, db_obj: InterviewDB) -> Interview:
        """Convert InterviewDB to Interview model"""
        return Interview(
            id=db_obj.id,
            employee_id=db_obj.employee_id,
            interview_type=InterviewType(db_obj.interview_type),
            status=InterviewStatus(db_obj.status),
            scheduled_date=db_obj.scheduled_date,
            questions=db_obj.questions or [],
            responses=db_obj.responses or {},
            duration_minutes=db_obj.duration_minutes,
            notes=db_obj.notes,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at
        )