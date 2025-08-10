from typing import Dict, List, Optional, Any
from ..models.employee import Employee, EmployeeProfile
from ..models.question import Question
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.question_repository import QuestionRepository
from ..utils.logger import get_logger

class HRDatabaseTools:
    """Database tools for HR operations that agents can use"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.employee_repo = EmployeeRepository()
        self.question_repo = QuestionRepository()
    
    async def get_employee_profile(self, employee_id: str) -> Optional[EmployeeProfile]:
        """Get employee profile for AI agents"""
        try:
            employee = await self.employee_repo.get_by_id(employee_id)
            if not employee:
                return None
            
            # Convert to simplified profile for agents
            return EmployeeProfile(
                id=employee.id,
                name=employee.name,
                position=employee.position,
                department=employee.department,
                level=employee.level,
                experience_years=employee.experience_years,
                skills=employee.skills,
                recent_performance=self._get_recent_performance(employee.performance_ratings),
                career_goals=await self._get_career_goals(employee_id)
            )
        except Exception as e:
            self.logger.error(f"Error getting employee profile: {str(e)}")
            return None
    
    async def get_job_requirements(self, position: str, department: str) -> Dict[str, Any]:
        """Get job requirements for a specific position"""
        # This would typically query a job requirements database
        # For now, we'll return mock data based on common patterns
        requirements_map = {
            ("Software Engineer", "engineering"): {
                "required_skills": ["Python", "JavaScript", "SQL", "Git"],
                "preferred_skills": ["React", "Docker", "AWS"],
                "experience_level": "2-5 years",
                "competencies": ["Technical Skills", "Problem Solving", "Communication"]
            },
            ("Marketing Manager", "marketing"): {
                "required_skills": ["Digital Marketing", "Analytics", "Campaign Management"],
                "preferred_skills": ["SEO", "Social Media", "Content Strategy"],
                "experience_level": "3-7 years", 
                "competencies": ["Leadership", "Strategic Thinking", "Communication"]
            }
        }
        
        return requirements_map.get((position, department), {
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "Variable",
            "competencies": ["Communication", "Problem Solving"]
        })
    
    async def get_similar_interviews(self, employee_profile: EmployeeProfile) -> List[Dict[str, Any]]:
        """Get similar past interviews for benchmarking"""
        # Query database for interviews of employees with similar profiles
        # This helps agents understand patterns and standards
        pass
    
    async def save_question_bank(self, questions: List[Dict[str, Any]]) -> bool:
        """Save generated questions to question bank for reuse"""
        try:
            for q in questions:
                await self.question_repo.create(q)
            return True
        except Exception as e:
            self.logger.error(f"Error saving questions: {str(e)}")
            return False
    
    def _get_recent_performance(self, performance_ratings: List[Dict]) -> Optional[Dict[str, Any]]:
        """Extract most recent performance data"""
        if not performance_ratings:
            return None
        
        # Get the most recent rating
        recent = sorted(performance_ratings, key=lambda x: x.get('date', ''), reverse=True)[0]
        return recent
    
    async def _get_career_goals(self, employee_id: str) -> List[str]:
        """Get employee's career goals from previous interviews or profiles"""
        # This would query career development records
        return []
