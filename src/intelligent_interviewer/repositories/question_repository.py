from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from .base_repository import BaseRepository
from ..models.question import Question, QuestionDB, QuestionType, QuestionCategory, DifficultyLevel

class QuestionRepository(BaseRepository[Question, QuestionDB]):
    """Repository for question data operations"""
    
    def __init__(self):
        super().__init__(Question, QuestionDB)
    
    async def get_by_type(self, question_type: QuestionType) -> List[Question]:
        """Get questions by type"""
        try:
            async with get_session() as session:
                query = select(QuestionDB).where(
                    and_(
                        QuestionDB.question_type == question_type.value,
                        QuestionDB.is_active == True
                    )
                )
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting questions by type {question_type}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve questions: {str(e)}")
    
    async def get_by_category(self, category: QuestionCategory) -> List[Question]:
        """Get questions by category"""
        try:
            async with get_session() as session:
                query = select(QuestionDB).where(
                    and_(
                        QuestionDB.category == category.value,
                        QuestionDB.is_active == True
                    )
                )
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting questions by category {category}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve questions: {str(e)}")
    
    async def get_by_difficulty(self, difficulty: DifficultyLevel) -> List[Question]:
        """Get questions by difficulty level"""
        try:
            async with get_session() as session:
                query = select(QuestionDB).where(
                    and_(
                        QuestionDB.difficulty == difficulty.value,
                        QuestionDB.is_active == True
                    )
                )
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting questions by difficulty {difficulty}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve questions: {str(e)}")
    
    async def get_for_position(self, position: str, department: str, level: str) -> List[Question]:
        """Get questions suitable for a specific position"""
        try:
            async with get_session() as session:
                query = select(QuestionDB).where(
                    and_(
                        QuestionDB.is_active == True,
                        or_(
                            QuestionDB.target_positions.contains([position]),
                            QuestionDB.target_departments.contains([department]),
                            QuestionDB.target_levels.contains([level])
                        )
                    )
                )
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting questions for position {position}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve questions: {str(e)}")
    
    async def get_filtered_questions(
        self, 
        question_type: Optional[QuestionType] = None,
        category: Optional[QuestionCategory] = None,
        difficulty: Optional[DifficultyLevel] = None,
        position: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 20
    ) -> List[Question]:
        """Get questions with multiple filters"""
        try:
            async with get_session() as session:
                conditions = [QuestionDB.is_active == True]
                
                if question_type:
                    conditions.append(QuestionDB.question_type == question_type.value)
                if category:
                    conditions.append(QuestionDB.category == category.value)
                if difficulty:
                    conditions.append(QuestionDB.difficulty == difficulty.value)
                if position:
                    conditions.append(QuestionDB.target_positions.contains([position]))
                if department:
                    conditions.append(QuestionDB.target_departments.contains([department]))
                
                query = select(QuestionDB).where(and_(*conditions)).limit(limit)
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error getting filtered questions: {str(e)}")
            raise DatabaseError(f"Failed to retrieve questions: {str(e)}")
    
    async def search_questions(self, search_term: str) -> List[Question]:
        """Search questions by text content"""
        try:
            async with get_session() as session:
                query = select(QuestionDB).where(
                    and_(
                        QuestionDB.is_active == True,
                        QuestionDB.question_text.contains(search_term)
                    )
                )
                result = await session.execute(query)
                db_objs = result.scalars().all()
                return [self._to_model(obj) for obj in db_objs]
        except Exception as e:
            self.logger.error(f"Error searching questions: {str(e)}")
            raise DatabaseError(f"Failed to search questions: {str(e)}")
    
    async def deactivate_question(self, question_id: str) -> bool:
        """Deactivate a question instead of deleting"""
        try:
            result = await self.update(question_id, {"is_active": False})
            return result is not None
        except Exception as e:
            self.logger.error(f"Error deactivating question: {str(e)}")
            return False
    
    async def get_random_questions(
        self, 
        count: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Question]:
        """Get random questions for interview generation"""
        try:
            # First get filtered questions
            if filters:
                questions = await self.get_filtered_questions(**filters, limit=100)
            else:
                questions = await self.get_all(limit=100)
            
            # Return random subset
            import random
            return random.sample(questions, min(count, len(questions)))
        except Exception as e:
            self.logger.error(f"Error getting random questions: {str(e)}")
            return []
    
    def _to_model(self, db_obj: QuestionDB) -> Question:
        """Convert QuestionDB to Question model"""
        return Question(
            id=db_obj.id,
            question_text=db_obj.question_text,
            question_type=QuestionType(db_obj.question_type),
            category=QuestionCategory(db_obj.category),
            difficulty=DifficultyLevel(db_obj.difficulty),
            target_positions=db_obj.target_positions or [],
            target_departments=db_obj.target_departments or [],
            target_levels=db_obj.target_levels or []
        )
