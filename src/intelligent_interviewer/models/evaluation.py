from sqlalchemy import Column, String, Integer, Float, Text, JSON
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class EvaluationCriteria(str, Enum):
    TECHNICAL_SKILLS = "technical_skills"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    LEADERSHIP = "leadership"
    TEAMWORK = "teamwork"
    ADAPTABILITY = "adaptability"
    CULTURAL_FIT = "cultural_fit"
    GROWTH_POTENTIAL = "growth_potential"

class RecommendationType(str, Enum):
    PROMOTION = "promotion"
    TRAINING = "training"
    MENTORING = "mentoring"
    ROLE_CHANGE = "role_change"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    RECOGNITION = "recognition"

class EvaluationDB(Base):
    __tablename__ = "evaluations"
    
    id = Column(String, primary_key=True)
    interview_id = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    scores = Column(JSON, nullable=False)  # Dict of criteria -> scores
    overall_score = Column(Float, nullable=False)
    strengths = Column(JSON, default=list)
    areas_for_improvement = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    confidence_level = Column(Float, default=0.8)  # AI confidence in evaluation
    created_at = Column(DateTime, default=datetime.utcnow)

class Evaluation(BaseModel):
    """Evaluation results from AI analysis"""
    interview_id: str
    employee_id: str
    scores: Dict[EvaluationCriteria, float] = Field(..., description="Scores for each criteria (0-10)")
    overall_score: float = Field(..., ge=0, le=10)
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    recommendations: List[Dict[str, Any]] = []
    confidence_level: float = Field(0.8, ge=0, le=1)
    detailed_analysis: Optional[Dict[str, Any]] = None

class RecommendationItem(BaseModel):
    """Individual recommendation"""
    type: RecommendationType
    priority: int = Field(..., ge=1, le=5, description="1=highest priority")
    description: str
    action_items: List[str] = []
    timeline: Optional[str] = None
    success_metrics: Optional[List[str]] = None