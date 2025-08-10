from textwrap import dedent
from typing import Dict, Any, List
from .base_agent import BaseHRAgent
from ..tools.hr_database import HRDatabaseTools
from ..tools.analytics import AnalyticsTools
from ..models.question import GeneratedQuestion, QuestionType, QuestionCategory
from ..models.interview import InterviewType

class QuestionGeneratorAgent(BaseHRAgent):
    """Agent responsible for generating tailored interview questions"""
    
    def __init__(self):
        super().__init__(
            name="Question Generator",
            role="Generate dynamic interview questions tailored to specific employees and roles",
            instructions=dedent("""
            You are an expert HR Question Generator with deep knowledge of:
            - Interview best practices across different roles and industries
            - Behavioral interview techniques (STAR method)
            - Technical assessment strategies
            - Legal compliance in interview processes
            
            Your responsibilities:
            1. Analyze employee profiles comprehensively
            2. Generate questions that are:
               - Relevant to the specific role and level
               - Appropriate for the interview type
               - Unbiased and legally compliant
               - Varied in difficulty and format
            3. Create different question types:
               - Technical competency questions
               - Behavioral/situational questions
               - Career development questions
               - Performance evaluation questions
            4. Ensure questions assess key competencies for the role
            5. Provide rationale for each question selection
            
            Always consider:
            - Employee's current level and experience
            - Department-specific requirements
            - Industry standards and trends
            - Cultural fit assessment
            - Growth potential evaluation
            
            Generate 8-12 high-quality questions per session.
            """),
            tools=[HRDatabaseTools(), AnalyticsTools()]
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tailored questions for an interview"""
        try:
            employee_id = context["employee_id"]
            interview_type = context["interview_type"]
            
            self.logger.info(f"Generating questions for employee {employee_id}, type: {interview_type}")
            
            # Get employee profile and job requirements
            hr_tools = HRDatabaseTools()
            employee_profile = await hr_tools.get_employee_profile(employee_id)
            job_requirements = await hr_tools.get_job_requirements(
                employee_profile.position, 
                employee_profile.department
            )
            
            # Get analytics for benchmarking
            analytics_tools = AnalyticsTools()
            dept_benchmarks = await analytics_tools.get_department_benchmarks(
                employee_profile.department
            )
            
            # Build comprehensive context for AI
            ai_context = f"""
            {self.format_employee_context(employee_profile)}
            
            INTERVIEW TYPE: {interview_type}
            
            JOB REQUIREMENTS:
            Required Skills: {', '.join(job_requirements.get('required_skills', []))}
            Preferred Skills: {', '.join(job_requirements.get('preferred_skills', []))}
            Key Competencies: {', '.join(job_requirements.get('competencies', []))}
            
            DEPARTMENT BENCHMARKS:
            Average Score: {dept_benchmarks.get('average_score', 'N/A')}
            Top Quartile: {dept_benchmarks.get('top_quartile', 'N/A')}
            
            Please generate appropriate interview questions for this context.
            Include a mix of question types and provide rationale for each question.
            """
            
            # Generate questions using AI agent
            response = await self.agent.arun(ai_context)
            
            # Parse and structure the response
            questions = self._parse_generated_questions(response.content, interview_type)
            
            return {
                "questions": questions,
                "metadata": {
                    "employee_id": employee_id,
                    "interview_type": interview_type,
                    "total_questions": len(questions),
                    "generated_at": context.get("timestamp"),
                    "agent_confidence": self._assess_question_quality(questions)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating questions: {str(e)}")
            raise
    
    def get_required_fields(self) -> List[str]:
        return ["employee_id", "interview_type"]
    
    def _parse_generated_questions(self, response_content: str, interview_type: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured questions"""
        # This would parse the AI response and structure it
        # For now, returning a mock structure
        questions = [
            {
                "id": f"q_{i}",
                "question_text": f"Sample question {i}",
                "question_type": QuestionType.BEHAVIORAL,
                "category": QuestionCategory.SKILLS_ASSESSMENT,
                "rationale": f"This question assesses...",
                "weight": 1,
                "expected_elements": ["specific examples", "quantifiable results"]
            }
            for i in range(8)
        ]
        return questions
    
    def _assess_question_quality(self, questions: List[Dict]) -> float:
        """Assess the quality/completeness of generated questions"""
        # Simple quality scoring based on variety and completeness
        if not questions:
            return 0.0
        
        # Check for variety in question types
        types = set(q.get("question_type") for q in questions)
        categories = set(q.get("category") for q in questions)
        
        variety_score = (len(types) + len(categories)) / 10  # Normalize
        completeness_score = len(questions) / 10  # Target 10 questions
        
        return min(1.0, (variety_score + completeness_score) / 2)
