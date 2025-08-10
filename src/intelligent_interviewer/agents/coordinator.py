from textwrap import dedent
from typing import Dict, Any, List
from .base_agent import BaseHRAgent
from ..tools.hr_database import HRDatabaseTools
from ..tools.analytics import AnalyticsTools
from ..models.evaluation import RecommendationType, RecommendationItem

class DecisionSupportAgent(BaseHRAgent):
    """Agent that provides AI-driven recommendations for HR decisions"""
    
    def __init__(self):
        super().__init__(
            name="Decision Support Analyst",
            role="Provide AI-driven evaluations and recommendations for HR decisions",
            instructions=dedent("""
            You are an expert HR Decision Support Analyst with deep expertise in:
            - Career development and progression planning
            - Performance management and improvement strategies
            - Training and development program design
            - Organizational fit and role optimization
            - Talent retention and engagement strategies
            
            Your recommendations should be:
            1. Data-driven and evidence-based
            2. Actionable with clear next steps
            3. Aligned with business objectives
            4. Considerate of individual growth goals
            5. Realistic and achievable within organizational constraints
            
            Provide recommendations for:
            - Career advancement (promotions, role changes)
            - Skill development and training needs
            - Performance improvement plans
            - Recognition and reward opportunities
            - Mentoring and coaching assignments
            - Team placement and project assignments
            
            Always consider:
            - Employee's current performance and potential
            - Organizational needs and constraints
            - Industry standards and best practices
            - ROI of recommended interventions
            - Timeline and success metrics
            
            Prioritize recommendations by impact and feasibility.
            """),
            tools=[HRDatabaseTools(), AnalyticsTools()]
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive HR recommendations"""
        try:
            employee_id = context["employee_id"]
            analysis = context["analysis"]
            
            self.logger.info(f"Generating recommendations for employee {employee_id}")
            
            # Get comprehensive employee context
            hr_tools = HRDatabaseTools()
            employee_profile = await hr_tools.get_employee_profile(employee_id)
            job_requirements = await hr_tools.get_job_requirements(
                employee_profile.position, employee_profile.department
            )
            
            # Get analytics for context
            analytics_tools = AnalyticsTools()
            dept_benchmarks = await analytics_tools.get_department_benchmarks(
                employee_profile.department
            )
            
            # Build recommendation context
            recommendation_context = f"""
            {self.format_employee_context(employee_profile)}
            
            INTERVIEW ANALYSIS RESULTS:
            Overall Assessment: {analysis.get('overall_assessment', {}).get('summary', 'N/A')}
            
            Criterion Scores:
            {self._format_scores(analysis.get('criterion_scores', {}))}
            
            Strengths:
            {self._format_strengths(analysis.get('detailed_feedback', {}).get('strengths', []))}
            
            Development Areas:
            {self._format_development_areas(analysis.get('detailed_feedback', {}).get('development_areas', []))}
            
            DEPARTMENT BENCHMARKS:
            Average Performance: {dept_benchmarks.get('average_score', 'N/A')}
            Top Performer Threshold: {dept_benchmarks.get('top_quartile', 'N/A')}
            
            JOB REQUIREMENTS:
            {job_requirements}
            
            Please provide comprehensive, prioritized recommendations for this employee's development and career progression.
            Include specific action items, timelines, and success metrics.
            """
            
            # Generate recommendations using AI
            response = await self.agent.arun(recommendation_context)
            
            # Structure recommendations
            recommendations = self._structure_recommendations(
                response.content, analysis, employee_profile
            )
            
            return {
                "recommendations": recommendations,
                "metadata": {
                    "employee_id": employee_id,
                    "total_recommendations": len(recommendations.get("items", [])),
                    "high_priority_count": len([r for r in recommendations.get("items", []) if r.get("priority", 5) <= 2]),
                    "generated_at": context.get("timestamp"),
                    "confidence_level": self._assess_recommendation_quality(recommendations)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    def get_required_fields(self) -> List[str]:
        return ["employee_id", "analysis"]
    
    def _format_scores(self, scores: Dict) -> str:
        """Format scores for AI context"""
        return "\n".join([f"- {criterion}: {score}/10" for criterion, score in scores.items()])
    
    def _format_strengths(self, strengths: List[Dict]) -> str:
        """Format strengths for AI context"""
        formatted = []
        for strength in strengths:
            formatted.append(f"- {strength.get('area', 'N/A')}: {strength.get('evidence', 'N/A')}")
        return "\n".join(formatted)
    
    def _format_development_areas(self, areas: List[Dict]) -> str:
        """Format development areas for AI context"""
        formatted = []
        for area in areas:
            formatted.append(f"- {area.get('area', 'N/A')}: {area.get('gap', 'N/A')}")
        return "\n".join(formatted)
    
    def _structure_recommendations(
        self, 
        ai_response: str, 
        analysis: Dict, 
        employee_profile: Any
    ) -> Dict[str, Any]:
        """Structure AI recommendations into organized format"""
        
        # Mock comprehensive recommendations structure
        return {
            "executive_summary": {
                "overall_recommendation": "Strong performer ready for increased responsibilities",
                "key_priorities": [
                    "Leadership development program enrollment",
                    "Technical mentoring assignment",
                    "Cross-functional project leadership"
                ],
                "expected_outcomes": "Promotion readiness within 12-18 months"
            },
            "items": [
                {
                    "type": RecommendationType.TRAINING,
                    "priority": 1,
                    "title": "Leadership Development Program",
                    "description": "Enroll in comprehensive leadership training to address management readiness gap",
                    "action_items": [
                        "Identify suitable internal leadership program",
                        "Schedule training sessions over next 6 months",
                        "Assign leadership mentor",
                        "Begin leading small cross-functional project"
                    ],
                    "timeline": "6 months",
                    "success_metrics": [
                        "Completion of leadership assessment",
                        "360-degree feedback improvement",
                        "Successful project delivery"
                    ],
                    "estimated_cost": "$3,000",
                    "roi_projection": "High - addresses key promotion requirement"
                },
                {
                    "type": RecommendationType.MENTORING,
                    "priority": 2,
                    "title": "Senior Technical Mentorship",
                    "description": "Pair with senior engineer to enhance advanced technical skills",
                    "action_items": [
                        "Identify senior mentor in architecture domain",
                        "Establish weekly 1-on-1 sessions",
                        "Create technical learning plan",
                        "Work on complex technical challenges together"
                    ],
                    "timeline": "12 months",
                    "success_metrics": [
                        "Technical skill assessment scores",
                        "Complex problem-solving demonstrations",
                        "Mentor feedback ratings"
                    ],
                    "estimated_cost": "$500",
                    "roi_projection": "High - enhances technical capabilities"
                },
                {
                    "type": RecommendationType.RECOGNITION,
                    "priority": 3,
                    "title": "Performance Recognition",
                    "description": "Acknowledge strong performance and communication skills",
                    "action_items": [
                        "Nominate for quarterly recognition award",
                        "Share success stories in team meetings",
                        "Consider for conference speaking opportunities",
                        "Document achievements in performance review"
                    ],
                    "timeline": "Immediate",
                    "success_metrics": [
                        "Award recognition received",
                        "Positive team feedback",
                        "Increased engagement scores"
                    ],
                    "estimated_cost": "$200",
                    "roi_projection": "Medium - improves retention and motivation"
                }
            ],
            "long_term_pathway": {
                "6_month_goals": [
                    "Complete leadership fundamentals training",
                    "Lead cross-functional project successfully",
                    "Demonstrate improved technical architecture skills"
                ],
                "12_month_goals": [
                    "Ready for senior role consideration",
                    "Mentor junior team members",
                    "Contribute to strategic technical decisions"
                ],
                "18_month_goals": [
                    "Promotion to senior/lead role",
                    "Take on team management responsibilities",
                    "Drive major technical initiatives"
                ]
            },
            "risk_mitigation": {
                "potential_risks": [
                    "Limited management experience may slow promotion timeline",
                    "High performer retention risk if growth stagnates"
                ],
                "mitigation_strategies": [
                    "Accelerated leadership development with stretch assignments",
                    "Regular career progression discussions",
                    "Competitive compensation review"
                ]
            }
        }
    
    def _assess_recommendation_quality(self, recommendations: Dict) -> float:
        """Assess the quality and completeness of recommendations"""
        items = recommendations.get("items", [])
        
        if not items:
            return 0.3
        
        # Check for variety in recommendation types
        types = set(item.get("type") for item in items)
        variety_score = min(1.0, len(types) / 3)  # Target 3+ different types
        
        # Check for completeness of each recommendation
        completeness_scores = []
        for item in items:
            score = 0
            if item.get("action_items"): score += 0.3
            if item.get("timeline"): score += 0.2
            if item.get("success_metrics"): score += 0.3
            if item.get("estimated_cost"): score += 0.1
            if item.get("roi_projection"): score += 0.1
            completeness_scores.append(score)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        # Check for prioritization
        priorities = [item.get("priority", 5) for item in items]
        has_prioritization = len(set(priorities)) > 1
        priority_score = 1.0 if has_prioritization else 0.5
        
        overall_quality = (variety_score + avg_completeness + priority_score) / 3
        return min(1.0, max(0.3, overall_quality))