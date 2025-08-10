from typing import Dict, List, Any
import numpy as np
from datetime import datetime, timedelta
from ..repositories.interview_repository import InterviewRepository
from ..repositories.employee_repository import EmployeeRepository

class AnalyticsTools:
    """Analytics tools for HR insights and benchmarking"""
    
    def __init__(self):
        self.interview_repo = InterviewRepository()
        self.employee_repo = EmployeeRepository()
    
    async def get_department_benchmarks(self, department: str) -> Dict[str, float]:
        """Get performance benchmarks for a department"""
        interviews = await self.interview_repo.get_by_department(department)
        
        if not interviews:
            return {"average_score": 7.0, "top_quartile": 8.5}
        
        scores = [i.overall_score for i in interviews if i.overall_score]
        
        return {
            "average_score": np.mean(scores),
            "median_score": np.median(scores),
            "top_quartile": np.percentile(scores, 75),
            "bottom_quartile": np.percentile(scores, 25)
        }
    
    async def get_skill_trends(self, skill: str, timeframe_days: int = 90) -> Dict[str, Any]:
        """Analyze trends for specific skills"""
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        interviews = await self.interview_repo.get_recent(cutoff_date)
        
        skill_mentions = 0
        skill_scores = []
        
        for interview in interviews:
            if skill.lower() in str(interview.analysis).lower():
                skill_mentions += 1
                # Extract skill-specific score if available
                if interview.scores and skill.lower() in interview.scores:
                    skill_scores.append(interview.scores[skill.lower()])
        
        return {
            "mentions": skill_mentions,
            "average_score": np.mean(skill_scores) if skill_scores else None,
            "demand_trend": "increasing" if skill_mentions > len(interviews) * 0.3 else "stable"
        }
