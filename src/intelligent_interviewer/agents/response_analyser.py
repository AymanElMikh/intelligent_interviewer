from textwrap import dedent
from typing import Dict, Any, List
from .base_agent import BaseHRAgent
from ..tools.hr_database import HRDatabaseTools
from ..tools.analytics import AnalyticsTools
from ..models.evaluation import EvaluationCriteria

class ResponseAnalyzerAgent(BaseHRAgent):
    """Agent responsible for analyzing employee interview responses"""
    
    def __init__(self):
        super().__init__(
            name="Response Analyzer",
            role="Analyze and interpret employee responses to extract key insights",
            instructions=dedent("""
            You are an expert Response Analyzer for HR interviews with expertise in:
            - Behavioral analysis and competency assessment
            - Communication skills evaluation
            - Technical skill demonstration recognition
            - Cultural fit indicators identification
            - Leadership and teamwork assessment
            
            Your analysis should:
            1. Evaluate responses against specific criteria:
               - Technical competency demonstration
               - Communication clarity and effectiveness
               - Problem-solving approach and methodology
               - Leadership potential and examples
               - Teamwork and collaboration skills
               - Cultural fit and value alignment
               - Growth mindset and adaptability
            
            2. Extract specific evidence:
               - Concrete examples and achievements
               - Quantifiable results and impacts
               - Skills demonstrated through stories
               - Behavioral patterns and approaches
               - Attitude and motivation indicators
            
            3. Identify strengths and development areas:
               - Clear strengths with supporting evidence
               - Areas for improvement with specific examples
               - Skill gaps compared to role requirements
               - Potential red flags or concerns
            
            4. Provide objective scoring (1-10 scale) for each criterion
            
            Always maintain professional objectivity and avoid bias.
            Base conclusions on specific evidence from responses.
            """),
            tools=[HRDatabaseTools(), AnalyticsTools()]
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze employee responses and provide detailed insights"""
        try:
            interview_id = context["interview_id"]
            responses = context["responses"]
            questions = context["questions"]
            
            self.logger.info(f"Analyzing responses for interview {interview_id}")
            
            # Get employee context
            hr_tools = HRDatabaseTools()
            employee_profile = await hr_tools.get_employee_profile(context["employee_id"])
            
            # Get benchmarking data
            analytics_tools = AnalyticsTools()
            dept_benchmarks = await analytics_tools.get_department_benchmarks(
                employee_profile.department
            )
            
            # Build analysis context
            analysis_context = f"""
            {self.format_employee_context(employee_profile)}
            
            INTERVIEW QUESTIONS AND RESPONSES:
            {self._format_qa_pairs(questions, responses)}
            
            DEPARTMENT BENCHMARKS:
            Average Score: {dept_benchmarks.get('average_score', 'N/A')}
            Top Performers Score: {dept_benchmarks.get('top_quartile', 'N/A')}
            
            Please provide a comprehensive analysis of these responses.
            Include specific scores for each evaluation criterion and detailed reasoning.
            """
            
            # Analyze using AI agent
            response = await self.agent.arun(analysis_context)
            
            # Structure the analysis results
            analysis_results = self._structure_analysis(response.content, responses)
            
            return {
                "analysis": analysis_results,
                "metadata": {
                    "interview_id": interview_id,
                    "analyzed_responses": len(responses),
                    "analysis_timestamp": context.get("timestamp"),
                    "confidence_level": self._calculate_confidence(analysis_results)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing responses: {str(e)}")
            raise
    
    def get_required_fields(self) -> List[str]:
        return ["interview_id", "responses", "questions", "employee_id"]
    
    def _format_qa_pairs(self, questions: List[Dict], responses: Dict[str, str]) -> str:
        """Format questions and responses for AI analysis"""
        formatted = []
        for i, question in enumerate(questions, 1):
            q_text = question.get("question_text", f"Question {i}")
            response = responses.get(str(i), responses.get(q_text, "No response"))
            formatted.append(f"""
            Q{i}: {q_text}
            Response: {response}
            Question Type: {question.get('question_type', 'Unknown')}
            ---
            """)
        return "\n".join(formatted)
    
    def _structure_analysis(self, ai_response: str, responses: Dict[str, str]) -> Dict[str, Any]:
        """Structure the AI analysis into organized results"""
        # This would parse the AI response and extract structured data
        # For now, returning a comprehensive mock structure
        
        return {
            "overall_assessment": {
                "summary": "Strong candidate with excellent technical skills and communication abilities",
                "key_highlights": [
                    "Demonstrated strong problem-solving approach",
                    "Clear communication with specific examples",
                    "Shows leadership potential"
                ],
                "areas_of_concern": [
                    "Limited experience with team management",
                    "Could provide more quantified results"
                ]
            },
            "criterion_scores": {
                EvaluationCriteria.TECHNICAL_SKILLS: 8.5,
                EvaluationCriteria.COMMUNICATION: 9.0,
                EvaluationCriteria.PROBLEM_SOLVING: 8.0,
                EvaluationCriteria.LEADERSHIP: 7.5,
                EvaluationCriteria.TEAMWORK: 8.5,
                EvaluationCriteria.ADAPTABILITY: 8.0,
                EvaluationCriteria.CULTURAL_FIT: 9.0,
                EvaluationCriteria.GROWTH_POTENTIAL: 8.5
            },
            "detailed_feedback": {
                "strengths": [
                    {
                        "area": "Technical Problem Solving",
                        "evidence": "Provided specific example of optimizing database queries",
                        "impact": "Demonstrated 60% performance improvement"
                    },
                    {
                        "area": "Communication",
                        "evidence": "Clear, structured responses with concrete examples",
                        "impact": "Easy to follow thought process"
                    }
                ],
                "development_areas": [
                    {
                        "area": "Leadership Experience", 
                        "gap": "Limited direct team management experience",
                        "recommendation": "Seek mentoring opportunities or lead cross-functional projects"
                    }
                ]
            },
            "response_quality": {
                "completeness": 0.9,  # How complete were the responses
                "specificity": 0.85,  # How specific/concrete were examples
                "relevance": 0.95     # How relevant to the questions
            }
        }
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence level in the analysis"""
        scores = analysis.get("criterion_scores", {})
        response_quality = analysis.get("response_quality", {})
        
        if not scores or not response_quality:
            return 0.5
        
        # Higher confidence if responses were complete and specific
        completeness = response_quality.get("completeness", 0.5)
        specificity = response_quality.get("specificity", 0.5)
        
        # More consistent scores indicate higher confidence
        score_variance = self._calculate_variance(list(scores.values()))
        consistency_factor = max(0.5, 1.0 - (score_variance / 10))
        
        confidence = (completeness + specificity + consistency_factor) / 3
        return min(1.0, max(0.3, confidence))
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance in scores"""
        if len(scores) < 2:
            return 0
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance ** 0.5
