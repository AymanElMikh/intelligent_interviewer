from abc import ABC, abstractmethod
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from typing import Dict, Any, List, Optional
from ..config.settings import settings
from ..utils.logger import get_logger
from ..models.employee import EmployeeProfile

class BaseHRAgent(ABC):
    """Base class for all HR agents with common functionality"""
    
    def __init__(self, name: str, role: str, instructions: str, tools: List = None):
        self.name = name
        self.role = role
        self.logger = get_logger(self.__class__.__name__)
        
        self.agent = Agent(
            name=name,
            role=role,
            model=OpenAIChat(id=settings.openai_model),
            tools=tools or [],
            add_name_to_instructions=True,
            instructions=instructions,
        )
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the given context and return results"""
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate input context - override in specific agents"""
        required_fields = self.get_required_fields()
        return all(field in context for field in required_fields)
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for this agent - override in specific agents"""
        return []
    
    def format_employee_context(self, employee_profile: EmployeeProfile) -> str:
        """Format employee profile for agent context"""
        return f"""
        EMPLOYEE PROFILE:
        Name: {employee_profile.name}
        Position: {employee_profile.position}
        Department: {employee_profile.department}
        Level: {employee_profile.level}
        Experience: {employee_profile.experience_years} years
        Skills: {', '.join(employee_profile.skills)}
        Recent Performance: {employee_profile.recent_performance or 'N/A'}
        Career Goals: {', '.join(employee_profile.career_goals or [])}
        """
