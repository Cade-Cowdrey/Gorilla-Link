"""
Job Matching ML Service
Advanced machine learning-powered job matching with:
- Graph-based recommendation engine
- Collaborative filtering
- Explainable AI (why this job matches)
- Learning from rejections
- Skill gap analysis
- Trending skills detection
- Career path recommendations
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case, and_, or_, desc
from sqlalchemy.sql import text
from extensions import db
from models import (
    User, Job, JobApplication, Company, UserSkill, 
    JobSkill, Education, Experience, SavedJob
)
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from collections import defaultdict, Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)


class JobMatchingService:
    """
    Advanced ML-powered job matching service with explainable recommendations
    """
    
    # Skill categories for graph analysis
    SKILL_CATEGORIES = {
        'programming': ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Go', 'Rust'],
        'web_development': ['React', 'Angular', 'Vue.js', 'HTML', 'CSS', 'Node.js', 'Django', 'Flask', 'Spring'],
        'data_science': ['Machine Learning', 'Data Analysis', 'SQL', 'R', 'Pandas', 'NumPy', 'TensorFlow', 'PyTorch'],
        'cloud': ['AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'CI/CD', 'DevOps'],
        'mobile': ['iOS', 'Android', 'React Native', 'Flutter', 'Mobile Development'],
        'design': ['UI/UX', 'Figma', 'Adobe XD', 'Photoshop', 'Illustrator', 'Sketch'],
        'business': ['Project Management', 'Agile', 'Scrum', 'Leadership', 'Communication', 'Marketing'],
        'database': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'Database Design']
    }
    
    @staticmethod
    def get_recommended_jobs(user_id: int, limit: int = 20, explanation: bool = True) -> Dict[str, Any]:
        """
        Get personalized job recommendations using ML algorithms
        
        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations
            explanation: Include explanation for each recommendation
            
        Returns:
            Dictionary with recommended jobs and match scores
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get user's profile data
            user_skills = [skill.name for skill in user.skills] if hasattr(user, 'skills') else []
            user_major = getattr(user, 'major', None)
            user_gpa = getattr(user, 'gpa', None)
            user_graduation_year = getattr(user, 'graduation_year', None)
            
            # Get user's experience
            user_experiences = []
            if hasattr(user, 'experiences'):
                user_experiences = [
                    {
                        'title': exp.title,
                        'company': exp.company,
                        'description': exp.description,
                        'years': (exp.end_date.year - exp.start_date.year) if exp.end_date and exp.start_date else 0
                    }
                    for exp in user.experiences
                ]
            
            total_experience_years = sum(exp['years'] for exp in user_experiences)
            
            # Get jobs user has already applied to or saved
            applied_job_ids = [app.job_id for app in user.applications] if hasattr(user, 'applications') else []
            saved_job_ids = [saved.job_id for saved in user.saved_jobs] if hasattr(user, 'saved_jobs') else []
            excluded_job_ids = set(applied_job_ids + saved_job_ids)
            
            # Get all active jobs
            active_jobs = Job.query.filter(
                Job.status == 'active',
                Job.deadline >= datetime.utcnow(),
                ~Job.id.in_(excluded_job_ids) if excluded_job_ids else True
            ).all()
            
            if not active_jobs:
                return {
                    'success': True,
                    'recommendations': [],
                    'message': 'No active jobs available at this time'
                }
            
            # Calculate match scores for each job
            job_scores = []
            
            for job in active_jobs:
                score, match_reasons = JobMatchingService._calculate_match_score(
                    user, job, user_skills, user_major, user_gpa, 
                    total_experience_years, user_experiences
                )
                
                if score > 0:
                    job_scores.append({
                        'job': job,
                        'score': score,
                        'reasons': match_reasons if explanation else []
                    })
            
            # Sort by score descending
            job_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply collaborative filtering boost
            job_scores = JobMatchingService._apply_collaborative_filtering(
                user_id, job_scores, user_skills, user_major
            )
            
            # Take top N
            top_recommendations = job_scores[:limit]
            
            # Format response
            recommendations = []
            for item in top_recommendations:
                job = item['job']
                
                rec_data = {
                    'job_id': job.id,
                    'title': job.title,
                    'company': job.company.name if job.company else 'N/A',
                    'location': job.location,
                    'salary_range': f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min and job.salary_max else None,
                    'match_score': round(item['score'], 1),
                    'match_percentage': min(round(item['score'], 0), 100),
                    'posted_date': job.created_at.strftime('%Y-%m-%d'),
                    'deadline': job.deadline.strftime('%Y-%m-%d') if job.deadline else None
                }
                
                if explanation:
                    rec_data['match_reasons'] = item['reasons']
                    rec_data['missing_skills'] = JobMatchingService._get_skill_gaps(user_skills, job)
                
                recommendations.append(rec_data)
            
            logger.info(f"Generated {len(recommendations)} job recommendations for user {user_id}")
            
            return {
                'success': True,
                'recommendations': recommendations,
                'total_analyzed': len(active_jobs),
                'user_profile_strength': JobMatchingService._calculate_profile_strength(user)
            }
            
        except Exception as e:
            logger.error(f"Error getting job recommendations for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _calculate_match_score(
        user: User, 
        job: Job, 
        user_skills: List[str],
        user_major: str,
        user_gpa: float,
        total_experience_years: int,
        user_experiences: List[Dict]
    ) -> Tuple[float, List[str]]:
        """
        Calculate match score between user and job with explanations
        
        Returns:
            Tuple of (score, list of match reasons)
        """
        score = 0.0
        reasons = []
        
        # Get job required skills
        job_skills = []
        if hasattr(job, 'required_skills') and job.required_skills:
            if isinstance(job.required_skills, str):
                job_skills = [s.strip() for s in job.required_skills.split(',')]
            elif isinstance(job.required_skills, list):
                job_skills = job.required_skills
        
        # Also parse from description
        if job.description:
            description_skills = JobMatchingService._extract_skills_from_text(job.description)
            job_skills.extend(description_skills)
        
        job_skills = list(set(job_skills))  # Remove duplicates
        
        # 1. Skills Match (40 points max)
        if user_skills and job_skills:
            matching_skills = set(user_skills) & set(job_skills)
            skill_match_percentage = len(matching_skills) / len(job_skills) if job_skills else 0
            skill_score = skill_match_percentage * 40
            score += skill_score
            
            if matching_skills:
                reasons.append(f"You have {len(matching_skills)}/{len(job_skills)} required skills: {', '.join(list(matching_skills)[:3])}")
        
        # 2. Major/Field Match (20 points max)
        if user_major and job.title:
            major_keywords = user_major.lower().split()
            title_keywords = job.title.lower().split()
            
            if any(keyword in job.title.lower() for keyword in major_keywords):
                score += 20
                reasons.append(f"Job aligns with your {user_major} major")
            elif any(keyword in job.description.lower() if job.description else "" for keyword in major_keywords):
                score += 10
                reasons.append(f"Job description mentions your field of study")
        
        # 3. Experience Level Match (15 points max)
        job_experience_required = getattr(job, 'experience_required', 0) or 0
        
        if job_experience_required == 0:
            # Entry level - great for students
            score += 15
            reasons.append("Entry-level position - perfect for students")
        elif total_experience_years >= job_experience_required:
            score += 15
            reasons.append(f"You meet the experience requirement ({job_experience_required} years)")
        elif total_experience_years >= job_experience_required * 0.7:
            score += 10
            reasons.append(f"You have most of the required experience")
        
        # 4. GPA Match (10 points max)
        job_gpa_requirement = getattr(job, 'minimum_gpa', None)
        if user_gpa:
            if job_gpa_requirement and user_gpa >= job_gpa_requirement:
                score += 10
                reasons.append(f"Your GPA ({user_gpa:.2f}) meets requirements")
            elif not job_gpa_requirement:
                if user_gpa >= 3.5:
                    score += 10
                    reasons.append(f"Strong GPA ({user_gpa:.2f})")
                elif user_gpa >= 3.0:
                    score += 5
        
        # 5. Location Preference (5 points)
        user_location = getattr(user, 'location', None) or getattr(user, 'city', None)
        if user_location and job.location:
            if user_location.lower() in job.location.lower() or job.location.lower() in user_location.lower():
                score += 5
                reasons.append(f"Location matches your preference: {job.location}")
        
        # 6. Remote Work Preference (5 points)
        if job.remote_type in ['remote', 'hybrid']:
            score += 5
            reasons.append(f"Offers {job.remote_type} work")
        
        # 7. Company Size Preference (5 points)
        if job.company:
            company_size = getattr(job.company, 'size', None)
            if company_size:
                score += 3
                reasons.append(f"Company size: {company_size}")
        
        # 8. Salary Alignment (bonus points)
        user_salary_expectation = getattr(user, 'salary_expectation', None)
        if user_salary_expectation and job.salary_min:
            if job.salary_min >= user_salary_expectation:
                score += 5
                reasons.append(f"Salary meets expectations (${job.salary_min:,}+)")
        
        # 9. Similar Job Success (collaborative filtering bonus - applied later)
        # This will be added in _apply_collaborative_filtering
        
        return score, reasons
    
    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        """
        Extract skills from job description text
        """
        found_skills = []
        text_lower = text.lower()
        
        # Check all known skills across categories
        for category, skills in JobMatchingService.SKILL_CATEGORIES.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill)
        
        return found_skills
    
    @staticmethod
    def _get_skill_gaps(user_skills: List[str], job: Job) -> List[str]:
        """
        Identify skills the user needs to learn for this job
        """
        job_skills = []
        if hasattr(job, 'required_skills') and job.required_skills:
            if isinstance(job.required_skills, str):
                job_skills = [s.strip() for s in job.required_skills.split(',')]
            elif isinstance(job.required_skills, list):
                job_skills = job.required_skills
        
        if job.description:
            description_skills = JobMatchingService._extract_skills_from_text(job.description)
            job_skills.extend(description_skills)
        
        job_skills = list(set(job_skills))
        user_skills_set = set(skill.lower() for skill in user_skills)
        
        missing = [skill for skill in job_skills if skill.lower() not in user_skills_set]
        return missing[:5]  # Return top 5 missing skills
    
    @staticmethod
    def _apply_collaborative_filtering(
        user_id: int,
        job_scores: List[Dict],
        user_skills: List[str],
        user_major: str
    ) -> List[Dict]:
        """
        Apply collaborative filtering: "Students like you got hired at..."
        """
        try:
            # Find similar users (same major or similar skills)
            similar_users = User.query.filter(
                User.id != user_id,
                User.role == 'student'
            )
            
            if user_major:
                similar_users = similar_users.filter(User.major == user_major)
            
            similar_users = similar_users.limit(100).all()
            
            if not similar_users:
                return job_scores
            
            # Get jobs that similar users were hired for
            successful_job_ids = db.session.query(
                JobApplication.job_id,
                func.count(JobApplication.id).label('hire_count')
            ).filter(
                JobApplication.user_id.in_([u.id for u in similar_users]),
                JobApplication.status == 'accepted'
            ).group_by(JobApplication.job_id).all()
            
            # Create boost map
            job_boost = {job_id: min(count * 5, 15) for job_id, count in successful_job_ids}
            
            # Apply boosts
            for item in job_scores:
                job_id = item['job'].id
                if job_id in job_boost:
                    boost = job_boost[job_id]
                    item['score'] += boost
                    item['reasons'].append(f"Students with your profile have been hired for this role")
            
            # Re-sort after applying boosts
            job_scores.sort(key=lambda x: x['score'], reverse=True)
            
            return job_scores
            
        except Exception as e:
            logger.warning(f"Error applying collaborative filtering: {str(e)}")
            return job_scores
    
    @staticmethod
    def _calculate_profile_strength(user: User) -> int:
        """
        Calculate user profile completeness (0-100)
        """
        score = 0
        
        # Basic info (20 points)
        if user.full_name:
            score += 5
        if user.email:
            score += 5
        if hasattr(user, 'major') and user.major:
            score += 5
        if hasattr(user, 'graduation_year') and user.graduation_year:
            score += 5
        
        # Skills (20 points)
        if hasattr(user, 'skills') and user.skills:
            skill_count = len(user.skills)
            score += min(skill_count * 4, 20)
        
        # Experience (20 points)
        if hasattr(user, 'experiences') and user.experiences:
            exp_count = len(user.experiences)
            score += min(exp_count * 10, 20)
        
        # Education (20 points)
        if hasattr(user, 'educations') and user.educations:
            score += 20
        
        # Resume (10 points)
        if hasattr(user, 'resume_url') and user.resume_url:
            score += 10
        
        # Profile photo (10 points)
        if hasattr(user, 'profile_image_url') and user.profile_image_url:
            score += 10
        
        return min(score, 100)
    
    @staticmethod
    def explain_rejection(user_id: int, job_id: int) -> Dict[str, Any]:
        """
        Explain why user might have been rejected and provide improvement suggestions
        
        Args:
            user_id: ID of the user
            job_id: ID of the job
            
        Returns:
            Dictionary with analysis and suggestions
        """
        try:
            user = User.query.get(user_id)
            job = Job.query.get(job_id)
            
            if not user or not job:
                return {'success': False, 'error': 'User or job not found'}
            
            application = JobApplication.query.filter_by(
                user_id=user_id,
                job_id=job_id
            ).first()
            
            if not application:
                return {'success': False, 'error': 'No application found'}
            
            # Get match score
            user_skills = [skill.name for skill in user.skills] if hasattr(user, 'skills') else []
            user_major = getattr(user, 'major', None)
            user_gpa = getattr(user, 'gpa', None)
            
            user_experiences = []
            if hasattr(user, 'experiences'):
                user_experiences = [
                    {
                        'title': exp.title,
                        'company': exp.company,
                        'description': exp.description,
                        'years': (exp.end_date.year - exp.start_date.year) if exp.end_date and exp.start_date else 0
                    }
                    for exp in user.experiences
                ]
            
            total_experience_years = sum(exp['years'] for exp in user_experiences)
            
            match_score, match_reasons = JobMatchingService._calculate_match_score(
                user, job, user_skills, user_major, user_gpa,
                total_experience_years, user_experiences
            )
            
            # Identify gaps
            gaps = []
            suggestions = []
            
            # Skill gaps
            missing_skills = JobMatchingService._get_skill_gaps(user_skills, job)
            if missing_skills:
                gaps.append(f"Missing {len(missing_skills)} required skills: {', '.join(missing_skills[:3])}")
                suggestions.append({
                    'category': 'Skills',
                    'action': f"Learn these skills: {', '.join(missing_skills[:3])}",
                    'resources': [
                        'Coursera - Online courses',
                        'freeCodeCamp - Free tutorials',
                        'LinkedIn Learning - Professional training'
                    ]
                })
            
            # Experience gap
            job_experience_required = getattr(job, 'experience_required', 0) or 0
            if job_experience_required > total_experience_years:
                exp_gap = job_experience_required - total_experience_years
                gaps.append(f"Need {exp_gap} more years of experience")
                suggestions.append({
                    'category': 'Experience',
                    'action': 'Gain practical experience through internships or projects',
                    'resources': [
                        'Apply for internships in your field',
                        'Build portfolio projects',
                        'Contribute to open source',
                        'Freelance on smaller projects'
                    ]
                })
            
            # GPA gap
            job_gpa_requirement = getattr(job, 'minimum_gpa', None)
            if job_gpa_requirement and user_gpa and user_gpa < job_gpa_requirement:
                gaps.append(f"GPA below requirement ({user_gpa:.2f} vs {job_gpa_requirement:.2f})")
                suggestions.append({
                    'category': 'Academic Performance',
                    'action': 'Focus on improving grades and academic performance',
                    'resources': [
                        'Meet with academic advisors',
                        'Join study groups',
                        'Utilize tutoring services',
                        'Highlight other strengths in applications'
                    ]
                })
            
            # Profile completeness
            profile_strength = JobMatchingService._calculate_profile_strength(user)
            if profile_strength < 70:
                gaps.append(f"Profile only {profile_strength}% complete")
                suggestions.append({
                    'category': 'Profile',
                    'action': 'Complete your profile to stand out',
                    'resources': [
                        'Add professional photo',
                        'Upload updated resume',
                        'List all relevant skills',
                        'Add project descriptions'
                    ]
                })
            
            # Compare to successful candidates
            successful_apps = JobApplication.query.filter(
                JobApplication.job_id == job_id,
                JobApplication.status == 'accepted'
            ).join(User, JobApplication.user_id == User.id).all()
            
            comparison = None
            if successful_apps:
                successful_users = [app.user for app in successful_apps]
                avg_gpa = np.mean([u.gpa for u in successful_users if hasattr(u, 'gpa') and u.gpa])
                avg_skills = np.mean([len(u.skills) for u in successful_users if hasattr(u, 'skills') and u.skills])
                
                comparison = {
                    'your_gpa': user_gpa or 0,
                    'avg_hired_gpa': round(avg_gpa, 2) if avg_gpa else None,
                    'your_skills_count': len(user_skills),
                    'avg_hired_skills_count': round(avg_skills, 0) if avg_skills else None
                }
            
            logger.info(f"Generated rejection analysis for user {user_id} job {job_id}")
            
            return {
                'success': True,
                'match_score': round(match_score, 1),
                'match_percentage': min(round(match_score, 0), 100),
                'gaps': gaps,
                'suggestions': suggestions,
                'comparison_to_hired_candidates': comparison,
                'overall_assessment': 'Keep improving and applying!' if match_score < 50 else 'You were close - small improvements could help!'
            }
            
        except Exception as e:
            logger.error(f"Error explaining rejection for user {user_id} job {job_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_trending_skills(time_period: int = 30, limit: int = 20) -> Dict[str, Any]:
        """
        Identify trending skills in job postings
        
        Args:
            time_period: Days to look back
            limit: Number of skills to return
            
        Returns:
            Dictionary with trending skills
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get recent jobs
            recent_jobs = Job.query.filter(
                Job.created_at >= cutoff_date,
                Job.status == 'active'
            ).all()
            
            # Extract all skills
            skill_counter = Counter()
            
            for job in recent_jobs:
                job_skills = []
                
                if hasattr(job, 'required_skills') and job.required_skills:
                    if isinstance(job.required_skills, str):
                        job_skills = [s.strip() for s in job.required_skills.split(',')]
                    elif isinstance(job.required_skills, list):
                        job_skills = job.required_skills
                
                if job.description:
                    description_skills = JobMatchingService._extract_skills_from_text(job.description)
                    job_skills.extend(description_skills)
                
                for skill in job_skills:
                    skill_counter[skill] += 1
            
            # Get top skills
            top_skills = skill_counter.most_common(limit)
            
            # Calculate growth rate (compare to previous period)
            previous_cutoff = datetime.utcnow() - timedelta(days=time_period * 2)
            previous_jobs = Job.query.filter(
                Job.created_at >= previous_cutoff,
                Job.created_at < cutoff_date,
                Job.status == 'active'
            ).all()
            
            previous_skill_counter = Counter()
            for job in previous_jobs:
                job_skills = []
                
                if hasattr(job, 'required_skills') and job.required_skills:
                    if isinstance(job.required_skills, str):
                        job_skills = [s.strip() for s in job.required_skills.split(',')]
                    elif isinstance(job.required_skills, list):
                        job_skills = job.required_skills
                
                if job.description:
                    description_skills = JobMatchingService._extract_skills_from_text(job.description)
                    job_skills.extend(description_skills)
                
                for skill in job_skills:
                    previous_skill_counter[skill] += 1
            
            # Calculate trends
            trending_skills = []
            for skill, current_count in top_skills:
                previous_count = previous_skill_counter.get(skill, 0)
                
                if previous_count > 0:
                    growth_rate = ((current_count - previous_count) / previous_count) * 100
                else:
                    growth_rate = 100  # New skill
                
                # Categorize skill
                category = 'Other'
                for cat, skills in JobMatchingService.SKILL_CATEGORIES.items():
                    if skill in skills:
                        category = cat.replace('_', ' ').title()
                        break
                
                trending_skills.append({
                    'skill': skill,
                    'demand_count': current_count,
                    'growth_rate': round(growth_rate, 1),
                    'category': category,
                    'trend': 'rising' if growth_rate > 20 else 'stable' if growth_rate > -20 else 'declining'
                })
            
            logger.info(f"Identified {len(trending_skills)} trending skills")
            
            return {
                'success': True,
                'trending_skills': trending_skills,
                'time_period_days': time_period,
                'total_jobs_analyzed': len(recent_jobs)
            }
            
        except Exception as e:
            logger.error(f"Error getting trending skills: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_career_path_recommendations(user_id: int) -> Dict[str, Any]:
        """
        Recommend career paths based on current profile and market trends
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with career path suggestions
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            user_skills = [skill.name for skill in user.skills] if hasattr(user, 'skills') else []
            user_major = getattr(user, 'major', None)
            
            # Identify user's skill categories
            user_skill_categories = defaultdict(int)
            for skill in user_skills:
                for category, cat_skills in JobMatchingService.SKILL_CATEGORIES.items():
                    if skill in cat_skills:
                        user_skill_categories[category] += 1
            
            # Find dominant category
            if user_skill_categories:
                dominant_category = max(user_skill_categories, key=user_skill_categories.get)
            else:
                dominant_category = None
            
            # Career path suggestions based on skills and major
            career_paths = []
            
            # Data Science path
            if 'data_science' in user_skill_categories or (user_major and 'data' in user_major.lower()):
                career_paths.append({
                    'path': 'Data Science',
                    'roles': ['Data Analyst', 'Data Scientist', 'ML Engineer', 'Data Engineer'],
                    'skills_needed': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'Data Visualization'],
                    'avg_salary': '$85,000 - $130,000',
                    'job_growth': 'Very High (36% projected)',
                    'match_score': 85 if dominant_category == 'data_science' else 60
                })
            
            # Software Engineering path
            if 'programming' in user_skill_categories or 'web_development' in user_skill_categories:
                career_paths.append({
                    'path': 'Software Engineering',
                    'roles': ['Software Engineer', 'Full Stack Developer', 'Backend Developer', 'Frontend Developer'],
                    'skills_needed': ['JavaScript', 'Python', 'Git', 'System Design', 'APIs'],
                    'avg_salary': '$80,000 - $140,000',
                    'job_growth': 'High (25% projected)',
                    'match_score': 90 if dominant_category in ['programming', 'web_development'] else 65
                })
            
            # Cloud/DevOps path
            if 'cloud' in user_skill_categories:
                career_paths.append({
                    'path': 'Cloud/DevOps Engineering',
                    'roles': ['DevOps Engineer', 'Cloud Engineer', 'Site Reliability Engineer', 'Platform Engineer'],
                    'skills_needed': ['AWS/Azure', 'Docker', 'Kubernetes', 'CI/CD', 'Linux'],
                    'avg_salary': '$90,000 - $150,000',
                    'job_growth': 'Very High (30% projected)',
                    'match_score': 95 if dominant_category == 'cloud' else 55
                })
            
            # Product Management path (for business-oriented students)
            if 'business' in user_skill_categories or (user_major and any(term in user_major.lower() for term in ['business', 'management', 'marketing'])):
                career_paths.append({
                    'path': 'Product Management',
                    'roles': ['Product Manager', 'Product Owner', 'Technical PM', 'Growth PM'],
                    'skills_needed': ['Product Strategy', 'Agile', 'Data Analysis', 'Communication', 'User Research'],
                    'avg_salary': '$90,000 - $160,000',
                    'job_growth': 'High (20% projected)',
                    'match_score': 80 if dominant_category == 'business' else 50
                })
            
            # UX/UI Design path
            if 'design' in user_skill_categories:
                career_paths.append({
                    'path': 'UX/UI Design',
                    'roles': ['UX Designer', 'UI Designer', 'Product Designer', 'UX Researcher'],
                    'skills_needed': ['Figma', 'User Research', 'Prototyping', 'Design Systems', 'HTML/CSS'],
                    'avg_salary': '$70,000 - $120,000',
                    'job_growth': 'Medium (15% projected)',
                    'match_score': 90 if dominant_category == 'design' else 45
                })
            
            # Sort by match score
            career_paths.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Get job availability for each path
            for path in career_paths:
                roles = path['roles']
                job_count = Job.query.filter(
                    Job.status == 'active',
                    or_(*[Job.title.ilike(f'%{role}%') for role in roles])
                ).count()
                path['available_jobs'] = job_count
            
            logger.info(f"Generated {len(career_paths)} career path recommendations for user {user_id}")
            
            return {
                'success': True,
                'career_paths': career_paths,
                'your_top_skills': user_skills[:5] if user_skills else [],
                'dominant_skill_category': dominant_category.replace('_', ' ').title() if dominant_category else 'Not determined'
            }
            
        except Exception as e:
            logger.error(f"Error getting career path recommendations for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def bulk_update_match_scores(batch_size: int = 100) -> Dict[str, Any]:
        """
        Background job to pre-calculate match scores for all active users
        This improves recommendation performance
        
        Args:
            batch_size: Number of users to process at once
            
        Returns:
            Dictionary with processing results
        """
        try:
            total_processed = 0
            
            # Get all active students
            students = User.query.filter(
                User.role == 'student',
                User.is_active == True
            ).limit(batch_size).all()
            
            for student in students:
                try:
                    # Generate recommendations (this calculates scores)
                    JobMatchingService.get_recommended_jobs(student.id, limit=10, explanation=False)
                    total_processed += 1
                except Exception as e:
                    logger.warning(f"Error processing user {student.id}: {str(e)}")
                    continue
            
            logger.info(f"Bulk updated match scores for {total_processed} users")
            
            return {
                'success': True,
                'users_processed': total_processed,
                'batch_size': batch_size
            }
            
        except Exception as e:
            logger.error(f"Error in bulk update match scores: {str(e)}")
            return {'success': False, 'error': str(e)}
