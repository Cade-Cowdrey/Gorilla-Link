"""
Alumni Career Tracking Service
Track alumni career trajectories and success stories:
- Career timeline visualization (ready for D3.js)
- Salary progression tracking
- Success story showcase
- Career path analysis
- Industry transition tracking
- "Where are they now" profiles
- Mentorship connections
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case, and_, or_, desc, extract
from sqlalchemy.sql import text
from extensions import db
from models import User, Job, JobApplication, Company, Experience, Education
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


class AlumniCareerTrackingService:
    """
    Service for tracking and visualizing alumni career trajectories
    """
    
    # Career level definitions
    CAREER_LEVELS = {
        'entry': ['Junior', 'Associate', 'Entry', 'Intern', 'Graduate', 'Trainee'],
        'mid': ['', 'Developer', 'Engineer', 'Analyst', 'Specialist', 'Coordinator'],
        'senior': ['Senior', 'Lead', 'Principal', 'Staff'],
        'management': ['Manager', 'Director', 'Head of', 'VP', 'Chief'],
        'executive': ['VP', 'SVP', 'EVP', 'Chief', 'President', 'CEO', 'CTO', 'CFO', 'COO']
    }
    
    # Industry categories
    INDUSTRIES = [
        'Technology', 'Healthcare', 'Finance', 'Education', 'Retail',
        'Manufacturing', 'Consulting', 'Government', 'Nonprofit', 'Media',
        'Real Estate', 'Energy', 'Transportation', 'Hospitality', 'Other'
    ]
    
    @staticmethod
    def get_alumni_profile(user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive alumni career profile
        
        Args:
            user_id: ID of the alumni user
            
        Returns:
            Dictionary with alumni career data
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if user is alumni
            if not getattr(user, 'is_alumni', False) and user.role != 'alumni':
                return {'success': False, 'error': 'User is not an alumni'}
            
            # Get career timeline
            career_timeline = AlumniCareerTrackingService._build_career_timeline(user)
            
            # Get education history
            education_history = []
            if hasattr(user, 'educations'):
                for edu in user.educations:
                    education_history.append({
                        'degree': edu.degree,
                        'major': edu.major,
                        'institution': edu.institution,
                        'graduation_year': edu.graduation_year,
                        'gpa': edu.gpa if hasattr(edu, 'gpa') else None
                    })
            
            # Calculate career metrics
            metrics = AlumniCareerTrackingService._calculate_career_metrics(career_timeline)
            
            # Get current position
            current_position = career_timeline[0] if career_timeline else None
            
            # Skills evolution
            skills = [skill.name for skill in user.skills] if hasattr(user, 'skills') else []
            
            logger.info(f"Retrieved alumni profile for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'name': user.full_name,
                'graduation_year': getattr(user, 'graduation_year', None),
                'major': getattr(user, 'major', None),
                'current_position': current_position,
                'career_timeline': career_timeline,
                'education_history': education_history,
                'skills': skills,
                'metrics': metrics,
                'profile_image': getattr(user, 'profile_image_url', None),
                'linkedin_url': getattr(user, 'linkedin_url', None)
            }
            
        except Exception as e:
            logger.error(f"Error getting alumni profile for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _build_career_timeline(user: User) -> List[Dict[str, Any]]:
        """
        Build chronological career timeline for D3.js visualization
        """
        timeline = []
        
        if not hasattr(user, 'experiences'):
            return timeline
        
        for exp in sorted(user.experiences, key=lambda x: x.start_date if x.start_date else datetime.min, reverse=True):
            # Determine career level
            career_level = AlumniCareerTrackingService._determine_career_level(exp.title)
            
            # Calculate duration
            if exp.end_date:
                duration_months = (exp.end_date.year - exp.start_date.year) * 12 + (exp.end_date.month - exp.start_date.month) if exp.start_date else 0
            else:
                # Current position
                duration_months = (datetime.utcnow().year - exp.start_date.year) * 12 + (datetime.utcnow().month - exp.start_date.month) if exp.start_date else 0
            
            timeline.append({
                'id': exp.id,
                'title': exp.title,
                'company': exp.company,
                'location': exp.location if hasattr(exp, 'location') else None,
                'start_date': exp.start_date.strftime('%Y-%m-%d') if exp.start_date else None,
                'end_date': exp.end_date.strftime('%Y-%m-%d') if exp.end_date else 'Present',
                'duration_months': duration_months,
                'career_level': career_level,
                'description': exp.description,
                'is_current': exp.end_date is None
            })
        
        return timeline
    
    @staticmethod
    def _determine_career_level(title: str) -> str:
        """
        Determine career level from job title
        """
        title_lower = title.lower()
        
        # Check executive first (most senior)
        for keyword in AlumniCareerTrackingService.CAREER_LEVELS['executive']:
            if keyword.lower() in title_lower:
                return 'executive'
        
        # Check management
        for keyword in AlumniCareerTrackingService.CAREER_LEVELS['management']:
            if keyword.lower() in title_lower:
                return 'management'
        
        # Check senior
        for keyword in AlumniCareerTrackingService.CAREER_LEVELS['senior']:
            if keyword.lower() in title_lower:
                return 'senior'
        
        # Check entry
        for keyword in AlumniCareerTrackingService.CAREER_LEVELS['entry']:
            if keyword.lower() in title_lower:
                return 'entry'
        
        # Default to mid-level
        return 'mid'
    
    @staticmethod
    def _calculate_career_metrics(timeline: List[Dict]) -> Dict[str, Any]:
        """
        Calculate career progression metrics
        """
        if not timeline:
            return {}
        
        # Total years of experience
        total_months = sum(pos['duration_months'] for pos in timeline)
        total_years = round(total_months / 12, 1)
        
        # Number of positions
        num_positions = len(timeline)
        
        # Average tenure
        avg_tenure_months = total_months / num_positions if num_positions > 0 else 0
        avg_tenure_years = round(avg_tenure_months / 12, 1)
        
        # Career progression (entry -> mid -> senior -> management -> executive)
        level_progression = [pos['career_level'] for pos in reversed(timeline)]
        
        # Number of companies
        unique_companies = len(set(pos['company'] for pos in timeline))
        
        # Current level
        current_level = timeline[0]['career_level'] if timeline else 'entry'
        
        return {
            'total_years_experience': total_years,
            'number_of_positions': num_positions,
            'average_tenure_years': avg_tenure_years,
            'unique_companies': unique_companies,
            'current_career_level': current_level,
            'level_progression': level_progression,
            'career_mobility': 'High' if unique_companies >= 3 else 'Medium' if unique_companies == 2 else 'Low'
        }
    
    @staticmethod
    def get_salary_progression(user_id: int) -> Dict[str, Any]:
        """
        Track salary progression over career
        
        Args:
            user_id: ID of the alumni user
            
        Returns:
            Dictionary with salary data points for visualization
        """
        try:
            user = User.query.get(user_id)
            if not user or not hasattr(user, 'experiences'):
                return {'success': False, 'error': 'User or experience data not found'}
            
            salary_data = []
            
            for exp in sorted(user.experiences, key=lambda x: x.start_date if x.start_date else datetime.min):
                # Get salary if available
                salary = getattr(exp, 'salary', None)
                
                if salary:
                    salary_data.append({
                        'date': exp.start_date.strftime('%Y-%m-%d') if exp.start_date else None,
                        'title': exp.title,
                        'company': exp.company,
                        'salary': salary,
                        'career_level': AlumniCareerTrackingService._determine_career_level(exp.title)
                    })
            
            # Calculate growth rate
            if len(salary_data) >= 2:
                first_salary = salary_data[0]['salary']
                last_salary = salary_data[-1]['salary']
                total_growth = ((last_salary - first_salary) / first_salary * 100) if first_salary > 0 else 0
                
                # Calculate years between first and last
                first_date = datetime.strptime(salary_data[0]['date'], '%Y-%m-%d')
                last_date = datetime.strptime(salary_data[-1]['date'], '%Y-%m-%d')
                years_diff = (last_date - first_date).days / 365.25
                
                avg_annual_growth = (total_growth / years_diff) if years_diff > 0 else 0
            else:
                total_growth = 0
                avg_annual_growth = 0
            
            logger.info(f"Retrieved salary progression for user {user_id}: {len(salary_data)} data points")
            
            return {
                'success': True,
                'salary_progression': salary_data,
                'total_growth_percentage': round(total_growth, 1),
                'avg_annual_growth_percentage': round(avg_annual_growth, 1),
                'data_points': len(salary_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting salary progression for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_success_stories(limit: int = 10, graduation_year: int = None, major: str = None) -> Dict[str, Any]:
        """
        Get featured alumni success stories
        
        Args:
            limit: Number of stories to return
            graduation_year: Filter by graduation year
            major: Filter by major
            
        Returns:
            Dictionary with success stories
        """
        try:
            # Query alumni users
            query = User.query.filter(
                or_(User.is_alumni == True, User.role == 'alumni')
            )
            
            if graduation_year:
                query = query.filter(User.graduation_year == graduation_year)
            
            if major:
                query = query.filter(User.major.ilike(f'%{major}%'))
            
            alumni = query.limit(limit * 2).all()  # Get more than needed for filtering
            
            success_stories = []
            
            for alum in alumni:
                # Get their career timeline
                timeline = AlumniCareerTrackingService._build_career_timeline(alum)
                
                if not timeline:
                    continue
                
                current_position = timeline[0]
                metrics = AlumniCareerTrackingService._calculate_career_metrics(timeline)
                
                # Calculate success score
                success_score = AlumniCareerTrackingService._calculate_success_score(alum, timeline, metrics)
                
                if success_score >= 50:  # Only include successful alumni
                    success_stories.append({
                        'user_id': alum.id,
                        'name': alum.full_name,
                        'graduation_year': getattr(alum, 'graduation_year', None),
                        'major': getattr(alum, 'major', None),
                        'current_title': current_position['title'],
                        'current_company': current_position['company'],
                        'years_since_graduation': datetime.utcnow().year - getattr(alum, 'graduation_year', datetime.utcnow().year),
                        'career_level': current_position['career_level'],
                        'total_experience_years': metrics.get('total_years_experience', 0),
                        'success_score': success_score,
                        'profile_image': getattr(alum, 'profile_image_url', None),
                        'story_headline': AlumniCareerTrackingService._generate_story_headline(alum, timeline),
                        'willing_to_mentor': getattr(alum, 'willing_to_mentor', False)
                    })
            
            # Sort by success score
            success_stories.sort(key=lambda x: x['success_score'], reverse=True)
            
            # Take top N
            success_stories = success_stories[:limit]
            
            logger.info(f"Retrieved {len(success_stories)} success stories")
            
            return {
                'success': True,
                'stories': success_stories,
                'total_count': len(success_stories)
            }
            
        except Exception as e:
            logger.error(f"Error getting success stories: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _calculate_success_score(user: User, timeline: List[Dict], metrics: Dict) -> float:
        """
        Calculate success score based on career progression
        """
        score = 0.0
        
        # Career level (40 points)
        level_scores = {
            'executive': 40,
            'management': 35,
            'senior': 25,
            'mid': 15,
            'entry': 5
        }
        score += level_scores.get(metrics.get('current_career_level', 'entry'), 5)
        
        # Years of experience (20 points)
        years_exp = metrics.get('total_years_experience', 0)
        score += min(years_exp * 2, 20)
        
        # Career mobility (20 points)
        mobility = metrics.get('career_mobility', 'Low')
        if mobility == 'High':
            score += 20
        elif mobility == 'Medium':
            score += 10
        
        # Company prestige (10 points) - simplified
        if timeline:
            current_company = timeline[0]['company']
            prestigious_companies = ['Google', 'Apple', 'Microsoft', 'Amazon', 'Meta', 'Netflix', 'Tesla']
            if any(company in current_company for company in prestigious_companies):
                score += 10
        
        # Skills count (10 points)
        if hasattr(user, 'skills'):
            skill_count = len(user.skills)
            score += min(skill_count, 10)
        
        return score
    
    @staticmethod
    def _generate_story_headline(user: User, timeline: List[Dict]) -> str:
        """
        Generate catchy headline for success story
        """
        if not timeline:
            return f"{user.full_name}'s Career Journey"
        
        current_pos = timeline[0]
        graduation_year = getattr(user, 'graduation_year', None)
        
        if graduation_year:
            years_since = datetime.utcnow().year - graduation_year
            return f"From Student to {current_pos['title']} in {years_since} Years"
        else:
            return f"Alumni Success: Now {current_pos['title']} at {current_pos['company']}"
    
    @staticmethod
    def get_career_paths_by_major(major: str) -> Dict[str, Any]:
        """
        Analyze common career paths for a specific major
        
        Args:
            major: The major/field of study
            
        Returns:
            Dictionary with career path analysis
        """
        try:
            # Get all alumni with this major
            alumni = User.query.filter(
                or_(User.is_alumni == True, User.role == 'alumni'),
                User.major.ilike(f'%{major}%')
            ).all()
            
            if not alumni:
                return {
                    'success': True,
                    'major': major,
                    'paths': [],
                    'message': 'No alumni data available for this major'
                }
            
            # Track career paths
            career_paths = defaultdict(int)
            industries = Counter()
            companies = Counter()
            job_titles = Counter()
            
            for alum in alumni:
                timeline = AlumniCareerTrackingService._build_career_timeline(alum)
                
                if timeline:
                    # Current position
                    current = timeline[0]
                    job_titles[current['title']] += 1
                    companies[current['company']] += 1
                    
                    # Determine industry (simplified)
                    company_name = current['company'].lower()
                    industry = AlumniCareerTrackingService._determine_industry(company_name)
                    industries[industry] += 1
                    
                    # Track progression path
                    if len(timeline) >= 2:
                        path = f"{timeline[-1]['title']} → {timeline[0]['title']}"
                        career_paths[path] += 1
            
            # Get top paths
            top_paths = [
                {'path': path, 'count': count, 'percentage': round(count / len(alumni) * 100, 1)}
                for path, count in career_paths.most_common(10)
            ]
            
            # Top industries
            top_industries = [
                {'industry': industry, 'count': count, 'percentage': round(count / len(alumni) * 100, 1)}
                for industry, count in industries.most_common(5)
            ]
            
            # Top companies
            top_companies = [
                {'company': company, 'count': count}
                for company, count in companies.most_common(10)
            ]
            
            # Top job titles
            top_titles = [
                {'title': title, 'count': count}
                for title, count in job_titles.most_common(10)
            ]
            
            logger.info(f"Analyzed career paths for {major}: {len(alumni)} alumni")
            
            return {
                'success': True,
                'major': major,
                'total_alumni': len(alumni),
                'common_career_paths': top_paths,
                'top_industries': top_industries,
                'top_employers': top_companies,
                'popular_job_titles': top_titles
            }
            
        except Exception as e:
            logger.error(f"Error getting career paths for major {major}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _determine_industry(company_name: str) -> str:
        """
        Determine industry from company name (simplified)
        """
        tech_keywords = ['tech', 'software', 'google', 'microsoft', 'apple', 'amazon', 'meta', 'facebook']
        finance_keywords = ['bank', 'capital', 'investment', 'financial', 'goldman', 'jpmorgan']
        healthcare_keywords = ['health', 'medical', 'hospital', 'pharma', 'clinic']
        consulting_keywords = ['consulting', 'mckinsey', 'bcg', 'bain', 'deloitte', 'accenture']
        
        for keyword in tech_keywords:
            if keyword in company_name:
                return 'Technology'
        
        for keyword in finance_keywords:
            if keyword in company_name:
                return 'Finance'
        
        for keyword in healthcare_keywords:
            if keyword in company_name:
                return 'Healthcare'
        
        for keyword in consulting_keywords:
            if keyword in company_name:
                return 'Consulting'
        
        return 'Other'
    
    @staticmethod
    def get_industry_transitions(user_id: int = None) -> Dict[str, Any]:
        """
        Track industry transitions in alumni careers
        
        Args:
            user_id: Optional user ID to get specific user's transitions
            
        Returns:
            Dictionary with industry transition data
        """
        try:
            if user_id:
                # Get specific user's transitions
                user = User.query.get(user_id)
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                alumni = [user]
            else:
                # Get all alumni
                alumni = User.query.filter(
                    or_(User.is_alumni == True, User.role == 'alumni')
                ).limit(500).all()
            
            all_transitions = []
            transition_counts = defaultdict(int)
            
            for alum in alumni:
                timeline = AlumniCareerTrackingService._build_career_timeline(alum)
                
                if len(timeline) >= 2:
                    # Track industry changes
                    for i in range(len(timeline) - 1):
                        current_company = timeline[i]['company'].lower()
                        next_company = timeline[i + 1]['company'].lower()
                        
                        current_industry = AlumniCareerTrackingService._determine_industry(current_company)
                        next_industry = AlumniCareerTrackingService._determine_industry(next_company)
                        
                        if current_industry != next_industry:
                            transition = f"{next_industry} → {current_industry}"
                            transition_counts[transition] += 1
                            
                            if user_id:
                                all_transitions.append({
                                    'from_industry': next_industry,
                                    'to_industry': current_industry,
                                    'from_company': timeline[i + 1]['company'],
                                    'to_company': timeline[i]['company'],
                                    'transition_date': timeline[i]['start_date']
                                })
            
            # Get top transitions
            top_transitions = [
                {'transition': trans, 'count': count}
                for trans, count in transition_counts.most_common(15)
            ]
            
            logger.info(f"Tracked {len(all_transitions)} industry transitions")
            
            return {
                'success': True,
                'user_specific': user_id is not None,
                'transitions': all_transitions if user_id else [],
                'top_transition_patterns': top_transitions,
                'total_transitions': len(all_transitions)
            }
            
        except Exception as e:
            logger.error(f"Error getting industry transitions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_salary_benchmarks(
        major: str = None,
        graduation_year: int = None,
        years_experience: int = None
    ) -> Dict[str, Any]:
        """
        Get salary benchmarks for alumni
        
        Args:
            major: Filter by major
            graduation_year: Filter by graduation year
            years_experience: Filter by years of experience
            
        Returns:
            Dictionary with salary statistics
        """
        try:
            # Build query
            query = User.query.filter(
                or_(User.is_alumni == True, User.role == 'alumni')
            )
            
            if major:
                query = query.filter(User.major.ilike(f'%{major}%'))
            
            if graduation_year:
                query = query.filter(User.graduation_year == graduation_year)
            
            alumni = query.all()
            
            # Collect salary data
            salaries = []
            salary_by_level = defaultdict(list)
            salary_by_industry = defaultdict(list)
            
            for alum in alumni:
                if not hasattr(alum, 'experiences'):
                    continue
                
                timeline = AlumniCareerTrackingService._build_career_timeline(alum)
                
                if not timeline:
                    continue
                
                # Filter by years of experience
                metrics = AlumniCareerTrackingService._calculate_career_metrics(timeline)
                alum_years_exp = metrics.get('total_years_experience', 0)
                
                if years_experience is not None:
                    if abs(alum_years_exp - years_experience) > 2:  # Within 2 years
                        continue
                
                # Get current salary
                current_position = timeline[0]
                
                # Try to get salary from experience
                for exp in alum.experiences:
                    if exp.title == current_position['title'] and exp.company == current_position['company']:
                        salary = getattr(exp, 'salary', None)
                        if salary and salary > 0:
                            salaries.append(salary)
                            salary_by_level[current_position['career_level']].append(salary)
                            
                            industry = AlumniCareerTrackingService._determine_industry(current_position['company'].lower())
                            salary_by_industry[industry].append(salary)
                            break
            
            if not salaries:
                return {
                    'success': True,
                    'message': 'No salary data available for specified criteria',
                    'filters': {
                        'major': major,
                        'graduation_year': graduation_year,
                        'years_experience': years_experience
                    }
                }
            
            # Calculate statistics
            salary_stats = {
                'median': statistics.median(salaries),
                'mean': statistics.mean(salaries),
                'min': min(salaries),
                'max': max(salaries),
                'percentile_25': statistics.quantiles(salaries, n=4)[0] if len(salaries) >= 4 else min(salaries),
                'percentile_75': statistics.quantiles(salaries, n=4)[2] if len(salaries) >= 4 else max(salaries),
                'sample_size': len(salaries)
            }
            
            # By career level
            level_stats = {}
            for level, level_salaries in salary_by_level.items():
                if level_salaries:
                    level_stats[level] = {
                        'median': statistics.median(level_salaries),
                        'mean': statistics.mean(level_salaries),
                        'count': len(level_salaries)
                    }
            
            # By industry
            industry_stats = {}
            for industry, ind_salaries in salary_by_industry.items():
                if ind_salaries:
                    industry_stats[industry] = {
                        'median': statistics.median(ind_salaries),
                        'mean': statistics.mean(ind_salaries),
                        'count': len(ind_salaries)
                    }
            
            logger.info(f"Generated salary benchmarks: {len(salaries)} data points")
            
            return {
                'success': True,
                'overall_statistics': {
                    'median_salary': f"${salary_stats['median']:,.0f}",
                    'mean_salary': f"${salary_stats['mean']:,.0f}",
                    'salary_range': f"${salary_stats['min']:,.0f} - ${salary_stats['max']:,.0f}",
                    'percentile_25': f"${salary_stats['percentile_25']:,.0f}",
                    'percentile_75': f"${salary_stats['percentile_75']:,.0f}",
                    'sample_size': salary_stats['sample_size']
                },
                'by_career_level': {
                    level: {
                        'median': f"${stats['median']:,.0f}",
                        'mean': f"${stats['mean']:,.0f}",
                        'count': stats['count']
                    }
                    for level, stats in level_stats.items()
                },
                'by_industry': {
                    industry: {
                        'median': f"${stats['median']:,.0f}",
                        'mean': f"${stats['mean']:,.0f}",
                        'count': stats['count']
                    }
                    for industry, stats in industry_stats.items()
                },
                'filters': {
                    'major': major,
                    'graduation_year': graduation_year,
                    'years_experience': years_experience
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting salary benchmarks: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_mentors(
        user_id: int,
        career_field: str = None,
        company: str = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find potential alumni mentors based on user's interests
        
        Args:
            user_id: ID of the user seeking mentorship
            career_field: Desired career field
            company: Target company
            limit: Number of mentors to return
            
        Returns:
            Dictionary with potential mentors
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            user_major = getattr(user, 'major', None)
            
            # Build mentor query
            query = User.query.filter(
                or_(User.is_alumni == True, User.role == 'alumni'),
                User.willing_to_mentor == True,
                User.id != user_id
            )
            
            # Filter by major if no specific field
            if not career_field and user_major:
                query = query.filter(User.major == user_major)
            
            potential_mentors = query.all()
            
            mentor_matches = []
            
            for mentor in potential_mentors:
                timeline = AlumniCareerTrackingService._build_career_timeline(mentor)
                
                if not timeline:
                    continue
                
                current_position = timeline[0]
                metrics = AlumniCareerTrackingService._calculate_career_metrics(timeline)
                
                # Calculate match score
                match_score = 0
                match_reasons = []
                
                # Major match
                if user_major and getattr(mentor, 'major', None) == user_major:
                    match_score += 30
                    match_reasons.append(f"Same major: {user_major}")
                
                # Career field match
                if career_field and career_field.lower() in current_position['title'].lower():
                    match_score += 40
                    match_reasons.append(f"Works in {career_field}")
                
                # Company match
                if company and company.lower() in current_position['company'].lower():
                    match_score += 30
                    match_reasons.append(f"Works at {company}")
                
                # Experience level (prefer senior alumni)
                career_level = metrics.get('current_career_level')
                if career_level and career_level in ['senior', 'management', 'executive']:
                    match_score += 20
                    match_reasons.append(f"{career_level.title()} level professional")
                
                # Years of experience
                years_exp = metrics.get('total_years_experience', 0)
                if years_exp >= 5:
                    match_score += 10
                    match_reasons.append(f"{years_exp} years of experience")
                
                if match_score >= 30:  # Minimum threshold
                    mentor_matches.append({
                        'user_id': mentor.id,
                        'name': mentor.full_name,
                        'current_title': current_position['title'],
                        'current_company': current_position['company'],
                        'graduation_year': getattr(mentor, 'graduation_year', None),
                        'major': getattr(mentor, 'major', None),
                        'years_experience': metrics.get('total_years_experience', 0),
                        'career_level': current_position['career_level'],
                        'match_score': match_score,
                        'match_reasons': match_reasons,
                        'profile_image': getattr(mentor, 'profile_image_url', None),
                        'linkedin_url': getattr(mentor, 'linkedin_url', None)
                    })
            
            # Sort by match score
            mentor_matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Take top N
            mentor_matches = mentor_matches[:limit]
            
            logger.info(f"Found {len(mentor_matches)} potential mentors for user {user_id}")
            
            return {
                'success': True,
                'mentors': mentor_matches,
                'total_found': len(mentor_matches),
                'search_criteria': {
                    'career_field': career_field,
                    'company': company,
                    'user_major': user_major
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding mentors for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
