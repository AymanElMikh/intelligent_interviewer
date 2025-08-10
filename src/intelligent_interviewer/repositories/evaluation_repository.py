from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from ..models.evaluation import Evaluation, EvaluationDB, EvaluationCriteria

class EvaluationRepository(BaseRepository[Evaluation, EvaluationDB]):
    """Repository for evaluation data operations"""
    
    def __init__(self):
        super().__init__(Evaluation, EvaluationDB)
    
    async def get_by_interview(self, interview_id: str) -> Optional[Evaluation]:
        """Get evaluation for a specific interview"""
        try:
            async with get_session() as session:
                query = select(EvaluationDB).where(EvaluationDB.interview_id == interview_id)
                result = await session.execute(query)
                db_obj = result.scalar_one_or_none()
                return self._to_model(db_obj) if db_obj else None
        except Exception as e:
            self.logger.error(f"Error getting evaluation for interview {interview_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve evaluation: {str(e)}")
    
    async def get_by_employee(self, employee_id: str) -> List[Evaluation]:
        """Get all evaluations for an employee"""
        try:
            async with get_session() as session:
                query = select(EvaluationDB).where(
                    EvaluationDB.employee_id == employee_id
                ).order_by(desc(EvaluationDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting evaluations for employee {employee_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve evaluations: {str(e)}")
    
    async def get_recent_evaluations(self, days: int = 30) -> List[Evaluation]:
        """Get recent evaluations within specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        try:
            async with get_session() as session:
                query = select(EvaluationDB).where(
                    EvaluationDB.created_at >= cutoff_date
                ).order_by(desc(EvaluationDB.created_at))
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting recent evaluations: {str(e)}")
            raise DatabaseError(f"Failed to retrieve evaluations: {str(e)}")
    
    def _to_model(self, db_obj: EvaluationDB) -> Evaluation:
        """Convert EvaluationDB to Evaluation model"""
        return Evaluation(
            id=db_obj.id,
            interview_id=db_obj.interview_id,
            employee_id=db_obj.employee_id,
            total_score=db_obj.total_score,
            criteria_scores=db_obj.criteria_scores,
            summary=db_obj.summary,
            strengths=db_obj.strengths or [],
            weaknesses=db_obj.weaknesses or [],
            recommendation=db_obj.recommendation,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at
        )
