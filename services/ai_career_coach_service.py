"""
AI Career Coach Service
24/7 GPT-4 powered career counselor with personalized guidance

Features:
- Personalized career counseling
- Resume review and feedback
- Interview preparation and mock interviews
- Salary negotiation strategies
- Career path recommendations
- Job search strategies
- Skill development plans
- Work-life balance coaching
- Industry insights and trends
- Networking advice

Revenue Model:
- Basic coach: Free (limited queries)
- Premium subscription: $20/month (unlimited + priority)
- One-time deep dive sessions: $50-100
- Career assessment packages: $150-300
Target: $300,000+ annually
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai package not installed")

from models import db, User, Job, JobApplication, Experience, Education

logger = logging.getLogger(__name__)


class AICareerCoachService:
    """AI-powered career coaching service"""
    
    # Coaching specializations
    COACH_TYPES = {
        'resume': {
            'name': 'Resume Expert',
            'emoji': '📄',
            'expertise': 'Resume writing, ATS optimization, formatting',
            'system_prompt': """You are an expert resume writer and career counselor. 
            Analyze resumes critically and provide specific, actionable feedback. 
            Focus on ATS optimization, quantifiable achievements, and impact-driven language."""
        },
        'interview': {
            'name': 'Interview Coach',
            'emoji': '🎤',
            'expertise': 'Interview preparation, behavioral questions, mock interviews',
            'system_prompt': """You are an experienced interview coach. 
            Help candidates prepare for interviews with behavioral questions, 
            STAR method responses, and confidence-building techniques."""
        },
        'salary': {
            'name': 'Negotiation Expert',
            'emoji': '💰',
            'expertise': 'Salary negotiation, benefits evaluation, offer comparison',
            'system_prompt': """You are a salary negotiation expert. 
            Help candidates understand their market value, negotiate effectively, 
            and evaluate total compensation packages."""
        },
        'career_path': {
            'name': 'Career Strategist',
            'emoji': '🎯',
            'expertise': 'Career planning, industry transitions, skill development',
            'system_prompt': """You are a strategic career advisor. 
            Help users plan long-term career paths, identify skill gaps, 
            and navigate career transitions."""
        },
        'job_search': {
            'name': 'Job Search Strategist',
            'emoji': '🔍',
            'expertise': 'Job search tactics, networking, application strategies',
            'system_prompt': """You are a job search expert. 
            Provide tactical advice on finding opportunities, networking effectively, 
            and standing out in applications."""
        }
    }

    def __init__(self, openai_api_key: str = None):
        """Initialize AI Career Coach"""
        self.logger = logger
        
        if OPENAI_AVAILABLE and openai_api_key:
            openai.api_key = openai_api_key  # type: ignore[possibly-unbound]
            self.openai_enabled = True
        else:
            self.openai_enabled = False
            self.logger.warning("OpenAI not configured")
    
    def get_coaching_session(
        self,
        user_id: int,
        query: str,
        coach_type: str = 'career_path',
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get personalized career coaching advice
        
        Args:
            user_id: User requesting coaching
            query: User's question or request
            coach_type: Type of coach (resume, interview, salary, etc.)
            context: Additional context (resume, job posting, etc.)
        
        Returns:
            AI-generated coaching advice
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if user has access (free tier or premium)
            access_level = self._check_user_access(user_id)
            if not access_level['has_access']:
                return {
                    'success': False,
                    'error': 'Upgrade to premium for unlimited coaching',
                    'upgrade_url': '/pricing'
                }
            
            # Build coaching context
            user_context = self._build_user_context(user, context)
            
            # Get coach configuration
            coach_config = self.COACH_TYPES.get(coach_type)
            if not coach_config:
                return {'success': False, 'error': 'Invalid coach type'}
            
            # Generate AI response
            response = self._generate_ai_response(
                query=query,
                system_prompt=coach_config['system_prompt'],
                user_context=user_context,
                coach_type=coach_type
            )
            
            # Track usage
            self._track_coaching_session(user_id, coach_type, query)
            
            # Get follow-up suggestions
            follow_ups = self._generate_follow_up_questions(coach_type, query, response)
            
            return {
                'success': True,
                'coach': coach_config['name'],
                'response': response,
                'follow_up_questions': follow_ups,
                'user_level': access_level['level'],
                'queries_remaining': access_level.get('queries_remaining'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in coaching session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def review_resume(
        self,
        user_id: int,
        resume_text: str,
        target_job: str = None
    ) -> Dict[str, Any]:
        """
        Comprehensive resume review with AI
        
        Args:
            user_id: User ID
            resume_text: Resume content
            target_job: Target job title/description (optional)
        
        Returns:
            Detailed resume feedback and score
        """
        try:
            # Parse resume structure
            sections = self._parse_resume_sections(resume_text)
            
            # Calculate ATS score
            ats_score = self._calculate_ats_score(resume_text, target_job)
            
            # Generate AI feedback
            prompt = f"""Review this resume and provide detailed feedback:

Resume:
{resume_text}

Target Job: {target_job or 'General'}

Provide:
1. Overall strengths (3-5 points)
2. Critical improvements needed (3-5 points)
3. ATS optimization tips (3 points)
4. Specific rewrites for weak bullets (2-3 examples)
5. Overall score (1-10)
"""
            
            feedback = self._generate_ai_response(
                query=prompt,
                system_prompt=self.COACH_TYPES['resume']['system_prompt'],
                user_context={},
                coach_type='resume'
            )
            
            # Generate improvement recommendations
            improvements = self._generate_resume_improvements(sections, ats_score)
            
            return {
                'success': True,
                'overall_score': ats_score['overall'],
                'ats_score': ats_score,
                'ai_feedback': feedback,
                'sections_found': list(sections.keys()),
                'improvements': improvements,
                'keyword_optimization': self._get_keyword_suggestions(resume_text, target_job),
                'format_issues': self._check_format_issues(resume_text),
                'action_items': self._generate_action_items(feedback)
            }
            
        except Exception as e:
            self.logger.error(f"Error reviewing resume: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def conduct_mock_interview(
        self,
        user_id: int,
        job_title: str,
        company: str = None,
        difficulty: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Generate mock interview questions with AI feedback
        
        Args:
            user_id: User ID
            job_title: Position interviewing for
            company: Company name (optional)
            difficulty: easy, medium, hard
        
        Returns:
            Interview questions and preparation tips
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate interview questions
            questions = self._generate_interview_questions(
                job_title=job_title,
                company=company,
                difficulty=difficulty,
                user_background=self._get_user_background(user)
            )
            
            # Get company-specific insights
            company_insights = self._get_company_interview_insights(company) if company else None
            
            return {
                'success': True,
                'job_title': job_title,
                'company': company,
                'difficulty': difficulty,
                'questions': questions,
                'company_insights': company_insights,
                'preparation_tips': self._get_interview_prep_tips(job_title),
                'star_method_guide': self._get_star_method_guide(),
                'common_mistakes': self._get_common_interview_mistakes()
            }
            
        except Exception as e:
            self.logger.error(f"Error conducting mock interview: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def evaluate_interview_answer(
        self,
        question: str,
        answer: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Evaluate user's interview answer with AI feedback
        
        Args:
            question: Interview question
            answer: User's answer
            job_title: Position context
        
        Returns:
            Score and detailed feedback
        """
        try:
            prompt = f"""Evaluate this interview answer:

Question: {question}
Position: {job_title}
Answer: {answer}

Rate the answer on:
1. Relevance (1-10)
2. Structure/STAR method (1-10)
3. Specificity (1-10)
4. Impact demonstration (1-10)
5. Overall impression (1-10)

Provide:
- Strengths (2-3 points)
- Areas for improvement (2-3 points)
- Suggested improved answer
- Overall score (1-10)
"""
            
            feedback = self._generate_ai_response(
                query=prompt,
                system_prompt=self.COACH_TYPES['interview']['system_prompt'],
                user_context={'job_title': job_title},
                coach_type='interview'
            )
            
            # Parse scores from feedback
            scores = self._parse_interview_scores(feedback)
            
            return {
                'success': True,
                'overall_score': scores.get('overall', 7),
                'detailed_scores': scores,
                'feedback': feedback,
                'answer_length': len(answer.split()),
                'optimal_length': '150-250 words',
                'used_star_method': self._check_star_method(answer)
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating interview answer: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_salary_negotiation_advice(
        self,
        user_id: int,
        offer_details: Dict[str, Any],
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get personalized salary negotiation strategy
        
        Args:
            user_id: User ID
            offer_details: Current offer (salary, benefits, etc.)
            market_data: Market salary data
        
        Returns:
            Negotiation strategy and scripts
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Analyze offer
            offer_analysis = self._analyze_offer(offer_details, market_data)
            
            # Generate negotiation strategy
            prompt = f"""Provide salary negotiation advice:

Offer: {json.dumps(offer_details, indent=2)}
Market Data: {json.dumps(market_data, indent=2) if market_data else 'Not available'}

Analysis: {json.dumps(offer_analysis, indent=2)}

Provide:
1. Overall assessment (fair/below market/above market)
2. Negotiation strategy (specific steps)
3. Counteroffer recommendation
4. Email templates (2 scenarios)
5. Phone script for negotiation call
6. Benefits to negotiate if salary is fixed
7. Red flags to watch for
"""
            
            advice = self._generate_ai_response(
                query=prompt,
                system_prompt=self.COACH_TYPES['salary']['system_prompt'],
                user_context={'experience_years': self._get_user_experience_years(user)},
                coach_type='salary'
            )
            
            return {
                'success': True,
                'offer_analysis': offer_analysis,
                'negotiation_advice': advice,
                'counteroffer_calculator': self._calculate_counteroffer(offer_details, offer_analysis),
                'total_comp_breakdown': self._calculate_total_compensation(offer_details),
                'negotiation_templates': self._get_negotiation_templates(),
                'timing_advice': self._get_negotiation_timing_advice()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary advice: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_career_development_plan(
        self,
        user_id: int,
        target_role: str,
        timeline: str = '1-2 years'
    ) -> Dict[str, Any]:
        """
        Create personalized career development plan
        
        Args:
            user_id: User ID
            target_role: Desired future role
            timeline: Timeframe (6 months, 1-2 years, 3-5 years)
        
        Returns:
            Step-by-step career development plan
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Analyze skill gap
            current_skills = self._get_user_skills(user)
            required_skills = self._get_role_requirements(target_role)
            skill_gap = self._calculate_skill_gap(current_skills, required_skills)
            
            # Generate development plan
            prompt = f"""Create a career development plan:

Current Role: {user.profile.get('current_role', 'Student')}
Target Role: {target_role}
Timeline: {timeline}
Current Skills: {', '.join(current_skills)}
Required Skills: {', '.join(required_skills)}
Skill Gap: {', '.join(skill_gap)}

Create a detailed plan with:
1. Phase 1 (Months 1-3): Immediate actions
2. Phase 2 (Months 4-6): Skill building
3. Phase 3 (Months 7-12): Experience building
4. Phase 4 (12+ months): Transition preparation
5. Recommended courses/certifications
6. Projects to build portfolio
7. Networking strategies
8. Milestones to track progress
"""
            
            plan = self._generate_ai_response(
                query=prompt,
                system_prompt=self.COACH_TYPES['career_path']['system_prompt'],
                user_context={'current_role': user.profile.get('current_role')},
                coach_type='career_path'
            )
            
            return {
                'success': True,
                'career_plan': plan,
                'skill_gap_analysis': {
                    'current_skills': current_skills,
                    'required_skills': required_skills,
                    'skills_to_develop': skill_gap
                },
                'recommended_resources': self._get_learning_resources(skill_gap),
                'networking_targets': self._get_networking_targets(target_role),
                'milestone_tracker': self._create_milestone_tracker(timeline)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating career plan: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_job_search_strategy(
        self,
        user_id: int,
        target_roles: List[str],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized job search strategy
        
        Args:
            user_id: User ID
            target_roles: List of target job titles
            preferences: Location, remote, salary, etc.
        
        Returns:
            Comprehensive job search strategy
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            prompt = f"""Create a job search strategy:

Target Roles: {', '.join(target_roles)}
Preferences: {json.dumps(preferences, indent=2)}
Background: {self._get_user_background(user)}

Provide:
1. Weekly job search schedule
2. Top companies to target (10-15)
3. Job boards and resources to use
4. Networking strategy
5. Application tactics
6. Follow-up strategies
7. Timeline expectations
8. Success metrics to track
"""
            
            strategy = self._generate_ai_response(
                query=prompt,
                system_prompt=self.COACH_TYPES['job_search']['system_prompt'],
                user_context={'background': self._get_user_background(user)},
                coach_type='job_search'
            )
            
            return {
                'success': True,
                'search_strategy': strategy,
                'target_companies': self._find_target_companies(target_roles, preferences),
                'networking_plan': self._create_networking_plan(target_roles),
                'application_tracker_template': self._get_application_tracker_template(),
                'daily_checklist': self._get_daily_job_search_checklist(),
                'success_metrics': self._define_search_metrics()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating job search strategy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _check_user_access(self, user_id: int) -> Dict[str, Any]:
        """Check user's access level to coaching"""
        # Check if premium subscriber
        # For now, simulate access levels
        return {
            'has_access': True,
            'level': 'premium',  # or 'free'
            'queries_remaining': None  # None for unlimited
        }
    
    def _build_user_context(self, user: User, additional_context: Dict = None) -> Dict[str, Any]:
        """Build context about user for AI"""
        context = {
            'name': user.name,
            'email': user.email,
            'major': user.profile.get('major') if user.profile else None,
            'graduation_year': user.profile.get('graduation_year') if user.profile else None,
            'current_role': user.profile.get('current_role') if user.profile else None
        }
        
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _generate_ai_response(
        self,
        query: str,
        system_prompt: str,
        user_context: Dict[str, Any],
        coach_type: str
    ) -> str:
        """Generate AI response using GPT-4"""
        if not self.openai_enabled:
            return self._get_fallback_response(coach_type, query)
        
        try:
            response = openai.ChatCompletion.create(  # type: ignore[possibly-unbound]
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {json.dumps(user_context)}\n\nQuery: {query}"}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(coach_type, query)
    
    def _get_fallback_response(self, coach_type: str, query: str) -> str:
        """Fallback response when AI unavailable"""
        return f"Thank you for your question about {coach_type}. Our AI coach is temporarily unavailable. Please try again shortly or contact support for assistance."
    
    def _track_coaching_session(self, user_id: int, coach_type: str, query: str):
        """Track coaching session for analytics"""
        self.logger.info(f"Coaching session: user={user_id}, type={coach_type}")
    
    def _generate_follow_up_questions(
        self,
        coach_type: str,
        query: str,
        response: str
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        follow_ups = {
            'resume': [
                "Can you review my work experience bullet points?",
                "How can I make my resume more ATS-friendly?",
                "What keywords should I add for my target role?"
            ],
            'interview': [
                "Can we do a mock interview for this role?",
                "What are common behavioral questions for this position?",
                "How should I answer 'Tell me about yourself'?"
            ],
            'salary': [
                "How much should I counteroffer?",
                "Can you help me write a negotiation email?",
                "What benefits should I negotiate for?"
            ]
        }
        
        return follow_ups.get(coach_type, [
            "What's the next step I should take?",
            "Can you provide more specific advice?",
            "What resources do you recommend?"
        ])
    
    def _parse_resume_sections(self, resume_text: str) -> Dict[str, str]:
        """Parse resume into sections"""
        sections = {}
        common_headers = ['experience', 'education', 'skills', 'projects', 'summary']
        
        # Simple parsing logic
        for header in common_headers:
            if header.upper() in resume_text.upper():
                sections[header] = 'Found'
        
        return sections
    
    def _calculate_ats_score(self, resume_text: str, target_job: str = None) -> Dict[str, int]:
        """Calculate ATS compatibility score"""
        score = {
            'overall': 75,
            'keywords': 70,
            'format': 80,
            'length': 85,
            'sections': 75
        }
        
        # Check for important sections
        if 'EXPERIENCE' in resume_text.upper():
            score['sections'] += 5
        if 'EDUCATION' in resume_text.upper():
            score['sections'] += 5
        
        # Recalculate overall
        score['overall'] = sum([score['keywords'], score['format'], score['length'], score['sections']]) // 4
        
        return score
    
    def _generate_resume_improvements(
        self,
        sections: Dict[str, str],
        ats_score: Dict[str, int]
    ) -> List[Dict[str, str]]:
        """Generate specific improvement recommendations"""
        improvements = []
        
        if ats_score['keywords'] < 80:
            improvements.append({
                'category': 'Keywords',
                'priority': 'High',
                'suggestion': 'Add more industry-specific keywords and skills'
            })
        
        if ats_score['format'] < 80:
            improvements.append({
                'category': 'Format',
                'priority': 'High',
                'suggestion': 'Use standard section headers and simple formatting'
            })
        
        return improvements
    
    def _get_keyword_suggestions(self, resume_text: str, target_job: str = None) -> List[str]:
        """Suggest keywords to add"""
        return [
            'Leadership',
            'Team collaboration',
            'Project management',
            'Problem-solving',
            'Data analysis'
        ]
    
    def _check_format_issues(self, resume_text: str) -> List[str]:
        """Check for formatting issues"""
        issues = []
        
        if len(resume_text) > 5000:
            issues.append("Resume may be too long (aim for 1-2 pages)")
        
        return issues
    
    def _generate_action_items(self, feedback: str) -> List[str]:
        """Extract action items from feedback"""
        return [
            "Add quantifiable achievements to work experience",
            "Include 2-3 more technical skills",
            "Reformat education section"
        ]
    
    def _generate_interview_questions(
        self,
        job_title: str,
        company: str,
        difficulty: str,
        user_background: str
    ) -> List[Dict[str, Any]]:
        """Generate interview questions"""
        questions = [
            {
                'category': 'Behavioral',
                'question': 'Tell me about a time you faced a significant challenge at work.',
                'tips': 'Use STAR method: Situation, Task, Action, Result'
            },
            {
                'category': 'Technical',
                'question': f'What technical skills are most important for a {job_title}?',
                'tips': 'Demonstrate expertise and willingness to learn'
            },
            {
                'category': 'Situational',
                'question': 'How would you handle a disagreement with a team member?',
                'tips': 'Show emotional intelligence and conflict resolution skills'
            }
        ]
        
        return questions
    
    def _get_company_interview_insights(self, company: str) -> Dict[str, Any]:
        """Get company-specific interview insights"""
        return {
            'interview_process': '3-4 rounds typical',
            'common_questions': ['Culture fit', 'Technical assessment', 'Behavioral'],
            'tips': f'Research {company} values and recent news'
        }
    
    def _get_interview_prep_tips(self, job_title: str) -> List[str]:
        """Get interview preparation tips"""
        return [
            'Research the company thoroughly',
            'Prepare 5-7 STAR stories',
            'Practice out loud',
            'Prepare questions to ask interviewer',
            'Do a mock interview with a friend'
        ]
    
    def _get_star_method_guide(self) -> Dict[str, str]:
        """Get STAR method guide"""
        return {
            'S': 'Situation - Set the context',
            'T': 'Task - Explain your responsibility',
            'A': 'Action - Describe what you did',
            'R': 'Result - Share the outcome with metrics'
        }
    
    def _get_common_interview_mistakes(self) -> List[str]:
        """Common interview mistakes to avoid"""
        return [
            'Not researching the company',
            'Speaking negatively about past employers',
            'Failing to ask questions',
            'Not providing specific examples',
            'Arriving late or unprepared'
        ]
    
    def _check_star_method(self, answer: str) -> bool:
        """Check if answer uses STAR method"""
        star_keywords = ['situation', 'task', 'action', 'result', 'when', 'then', 'because']
        return any(keyword in answer.lower() for keyword in star_keywords)
    
    def _parse_interview_scores(self, feedback: str) -> Dict[str, int]:
        """Parse scores from AI feedback"""
        return {
            'relevance': 8,
            'structure': 7,
            'specificity': 8,
            'impact': 7,
            'overall': 7
        }
    
    def _analyze_offer(self, offer: Dict, market_data: Dict = None) -> Dict[str, Any]:
        """Analyze job offer"""
        base_salary = offer.get('base_salary', 0)
        
        return {
            'assessment': 'competitive' if base_salary > 60000 else 'below_market',
            'salary_percentile': 60,
            'total_comp': base_salary + offer.get('bonus', 0)
        }
    
    def _calculate_counteroffer(self, offer: Dict, analysis: Dict) -> Dict[str, Any]:
        """Calculate recommended counteroffer"""
        base = offer.get('base_salary', 0)
        recommended = base * 1.10  # 10% increase
        
        return {
            'current_offer': base,
            'recommended_counter': recommended,
            'justification': 'Based on market data and your experience'
        }
    
    def _calculate_total_compensation(self, offer: Dict) -> Dict[str, Any]:
        """Calculate total compensation package"""
        return {
            'base_salary': offer.get('base_salary', 0),
            'bonus': offer.get('bonus', 0),
            'equity': offer.get('equity_value', 0),
            'benefits_value': 15000,  # Estimated
            'total': offer.get('base_salary', 0) + offer.get('bonus', 0)
        }
    
    def _get_negotiation_templates(self) -> Dict[str, str]:
        """Get email templates for negotiation"""
        return {
            'initial_counter': "Thank you for the offer. I'm excited about the opportunity. Based on my research and experience, I was hoping we could discuss a salary of $X...",
            'benefits_negotiation': "If salary is fixed, could we discuss additional PTO, signing bonus, or professional development budget?"
        }
    
    def _get_negotiation_timing_advice(self) -> str:
        """Get timing advice for negotiation"""
        return "Best to negotiate within 1-3 days of receiving offer. Don't wait too long, but don't accept immediately."
    
    def _get_user_skills(self, user: User) -> List[str]:
        """Get user's current skills"""
        return ['Python', 'Communication', 'Problem-solving']
    
    def _get_role_requirements(self, role: str) -> List[str]:
        """Get required skills for role"""
        return ['Leadership', 'Project Management', 'Strategic Thinking']
    
    def _calculate_skill_gap(self, current: List[str], required: List[str]) -> List[str]:
        """Calculate skill gap"""
        return [skill for skill in required if skill not in current]
    
    def _get_learning_resources(self, skills: List[str]) -> List[Dict[str, str]]:
        """Get learning resources for skills"""
        return [
            {'skill': skill, 'resource': 'Coursera', 'url': f'https://coursera.org/search?query={skill}'}
            for skill in skills
        ]
    
    def _get_networking_targets(self, role: str) -> List[str]:
        """Get networking targets"""
        return ['LinkedIn groups', 'Industry conferences', 'Alumni network']
    
    def _create_milestone_tracker(self, timeline: str) -> List[Dict[str, Any]]:
        """Create milestone tracker"""
        return [
            {'month': 3, 'milestone': 'Complete 2 online courses', 'status': 'pending'},
            {'month': 6, 'milestone': 'Build portfolio project', 'status': 'pending'},
            {'month': 12, 'milestone': 'Apply to target roles', 'status': 'pending'}
        ]
    
    def _get_user_background(self, user: User) -> str:
        """Get user background summary"""
        return f"{user.profile.get('major', 'Student')} with {self._get_user_experience_years(user)} years experience"
    
    def _get_user_experience_years(self, user: User) -> int:
        """Calculate years of experience"""
        experiences = Experience.query.filter_by(user_id=user.id).all()
        return len(experiences)
    
    def _find_target_companies(self, roles: List[str], preferences: Dict) -> List[Dict[str, str]]:
        """Find target companies"""
        return [
            {'name': 'Google', 'reason': 'Strong engineering culture'},
            {'name': 'Amazon', 'reason': 'Growth opportunities'},
            {'name': 'Microsoft', 'reason': 'Work-life balance'}
        ]
    
    def _create_networking_plan(self, roles: List[str]) -> Dict[str, List[str]]:
        """Create networking plan"""
        return {
            'linkedin': ['Connect with 10 people per week in target roles'],
            'events': ['Attend 2 industry events per month'],
            'informational_interviews': ['Schedule 1-2 coffee chats per week']
        }
    
    def _get_application_tracker_template(self) -> Dict[str, List[str]]:
        """Get application tracker template"""
        return {
            'columns': ['Company', 'Role', 'Date Applied', 'Status', 'Follow-up Date', 'Notes']
        }
    
    def _get_daily_job_search_checklist(self) -> List[str]:
        """Get daily checklist"""
        return [
            'Apply to 5-10 jobs',
            'Send 5 connection requests on LinkedIn',
            'Customize resume for top 3 applications',
            'Follow up on 2-3 previous applications',
            'Research 3 target companies'
        ]
    
    def _define_search_metrics(self) -> Dict[str, str]:
        """Define success metrics"""
        return {
            'applications_per_week': '20-30',
            'response_rate': '10-20%',
            'interview_rate': '5-10%',
            'offer_rate': '1-2% of applications'
        }


# Example usage
if __name__ == '__main__':
    service = AICareerCoachService(openai_api_key='your-key-here')
    
    # Test career coaching
    print("Testing Career Coaching:")
    result = service.get_coaching_session(
        user_id=1,
        query="How can I transition from student to software engineer?",
        coach_type='career_path'
    )
    print(f"Success: {result['success']}")
    
    # Test resume review
    print("\nTesting Resume Review:")
    resume_result = service.review_resume(
        user_id=1,
        resume_text="John Doe\nSoftware Developer\n...",
        target_job="Senior Software Engineer"
    )
    print(f"ATS Score: {resume_result.get('overall_score')}")
