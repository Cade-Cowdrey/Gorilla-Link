"""
Employer Analytics Service
Provides comprehensive analytics dashboards for employers including:
- Pipeline visualization with conversion rates
- Time-to-hire and cost-per-hire metrics
- Source effectiveness tracking
- Diversity and inclusion metrics
- Industry benchmarking
- Predictive hiring forecasting
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case, extract, and_, or_
from sqlalchemy.sql import text
from extensions import db
from models import (
    User, Job, JobApplication, Company, Event, EventAttendee,
    ScholarshipApplication, Message, Notification
)
import logging
from typing import Dict, List, Optional, Any
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmployerAnalyticsService:
    """
    Service for generating comprehensive analytics for employers
    """
    
    # Pipeline stage definitions
    PIPELINE_STAGES = [
        'posted', 'viewed', 'applied', 'screening', 
        'interview', 'offer', 'hired', 'rejected'
    ]
    
    # Industry benchmarks (national averages)
    INDUSTRY_BENCHMARKS = {
        'time_to_hire_days': {
            'Technology': 42,
            'Healthcare': 38,
            'Finance': 35,
            'Retail': 28,
            'Manufacturing': 45,
            'Education': 50,
            'Other': 40
        },
        'cost_per_hire': {
            'Technology': 4500,
            'Healthcare': 3800,
            'Finance': 5200,
            'Retail': 2800,
            'Manufacturing': 3500,
            'Education': 3000,
            'Other': 4000
        },
        'offer_acceptance_rate': {
            'Technology': 0.85,
            'Healthcare': 0.88,
            'Finance': 0.82,
            'Retail': 0.90,
            'Manufacturing': 0.87,
            'Education': 0.89,
            'Other': 0.85
        },
        'candidate_quality_score': {
            'Technology': 7.8,
            'Healthcare': 7.5,
            'Finance': 8.1,
            'Retail': 7.0,
            'Manufacturing': 7.2,
            'Education': 7.6,
            'Other': 7.5
        }
    }
    
    @staticmethod
    def generate_pipeline_metrics(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Generate comprehensive pipeline visualization metrics
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back (default 90)
            
        Returns:
            Dictionary with pipeline stages, conversion rates, and funnel data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get all jobs for this employer
            jobs = Job.query.filter(
                Job.employer_id == employer_id,
                Job.created_at >= cutoff_date
            ).all()
            
            job_ids = [job.id for job in jobs]
            
            if not job_ids:
                return {
                    'success': True,
                    'pipeline': [],
                    'conversion_rates': {},
                    'total_candidates': 0,
                    'time_period_days': time_period
                }
            
            # Count candidates at each stage
            pipeline_data = []
            
            # Stage 1: Jobs Posted
            jobs_posted = len(jobs)
            pipeline_data.append({
                'stage': 'posted',
                'stage_name': 'Jobs Posted',
                'count': jobs_posted,
                'percentage': 100.0
            })
            
            # Stage 2: Job Views (from analytics)
            job_views = db.session.query(func.sum(Job.view_count)).filter(
                Job.id.in_(job_ids)
            ).scalar() or 0
            pipeline_data.append({
                'stage': 'viewed',
                'stage_name': 'Job Views',
                'count': job_views,
                'percentage': 100.0  # Base for conversion
            })
            
            # Stage 3: Applications
            applications = JobApplication.query.filter(
                JobApplication.job_id.in_(job_ids),
                JobApplication.created_at >= cutoff_date
            ).all()
            
            total_applications = len(applications)
            pipeline_data.append({
                'stage': 'applied',
                'stage_name': 'Applications',
                'count': total_applications,
                'percentage': (total_applications / job_views * 100) if job_views > 0 else 0
            })
            
            # Stage 4: Screening
            screening_count = sum(1 for app in applications if app.status in ['under_review', 'screening'])
            pipeline_data.append({
                'stage': 'screening',
                'stage_name': 'In Screening',
                'count': screening_count,
                'percentage': (screening_count / total_applications * 100) if total_applications > 0 else 0
            })
            
            # Stage 5: Interviews
            interview_count = sum(1 for app in applications if app.status == 'interview')
            pipeline_data.append({
                'stage': 'interview',
                'stage_name': 'Interviews',
                'count': interview_count,
                'percentage': (interview_count / total_applications * 100) if total_applications > 0 else 0
            })
            
            # Stage 6: Offers
            offer_count = sum(1 for app in applications if app.status == 'offer')
            pipeline_data.append({
                'stage': 'offer',
                'stage_name': 'Offers Made',
                'count': offer_count,
                'percentage': (offer_count / total_applications * 100) if total_applications > 0 else 0
            })
            
            # Stage 7: Hired
            hired_count = sum(1 for app in applications if app.status == 'accepted')
            pipeline_data.append({
                'stage': 'hired',
                'stage_name': 'Hired',
                'count': hired_count,
                'percentage': (hired_count / total_applications * 100) if total_applications > 0 else 0
            })
            
            # Stage 8: Rejected
            rejected_count = sum(1 for app in applications if app.status == 'rejected')
            pipeline_data.append({
                'stage': 'rejected',
                'stage_name': 'Rejected',
                'count': rejected_count,
                'percentage': (rejected_count / total_applications * 100) if total_applications > 0 else 0
            })
            
            # Calculate conversion rates between stages
            conversion_rates = {
                'view_to_apply': (total_applications / job_views * 100) if job_views > 0 else 0,
                'apply_to_screen': (screening_count / total_applications * 100) if total_applications > 0 else 0,
                'screen_to_interview': (interview_count / screening_count * 100) if screening_count > 0 else 0,
                'interview_to_offer': (offer_count / interview_count * 100) if interview_count > 0 else 0,
                'offer_to_hire': (hired_count / offer_count * 100) if offer_count > 0 else 0,
                'overall_hire_rate': (hired_count / total_applications * 100) if total_applications > 0 else 0
            }
            
            # Top performing jobs
            top_jobs = db.session.query(
                Job.id,
                Job.title,
                func.count(JobApplication.id).label('application_count')
            ).join(JobApplication, Job.id == JobApplication.job_id).filter(
                Job.id.in_(job_ids)
            ).group_by(Job.id, Job.title).order_by(
                func.count(JobApplication.id).desc()
            ).limit(5).all()
            
            top_jobs_data = [
                {
                    'job_id': job.id,
                    'title': job.title,
                    'applications': job.application_count
                }
                for job in top_jobs
            ]
            
            logger.info(f"Generated pipeline metrics for employer {employer_id}: {total_applications} total applications")
            
            return {
                'success': True,
                'pipeline': pipeline_data,
                'conversion_rates': conversion_rates,
                'total_candidates': total_applications,
                'total_hires': hired_count,
                'time_period_days': time_period,
                'top_jobs': top_jobs_data,
                'active_jobs': jobs_posted
            }
            
        except Exception as e:
            logger.error(f"Error generating pipeline metrics for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_roi(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Calculate Return on Investment metrics
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back
            
        Returns:
            Dictionary with cost per hire, time to hire, quality metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get employer company
            employer = User.query.get(employer_id)
            if not employer or not employer.company_id:
                return {'success': False, 'error': 'Employer not found or no company'}
            
            company = Company.query.get(employer.company_id)
            
            # Get all applications that resulted in hires
            hired_applications = JobApplication.query.join(Job).filter(
                Job.employer_id == employer_id,
                JobApplication.status == 'accepted',
                JobApplication.updated_at >= cutoff_date
            ).all()
            
            total_hires = len(hired_applications)
            
            if total_hires == 0:
                return {
                    'success': True,
                    'total_hires': 0,
                    'cost_per_hire': 0,
                    'average_time_to_hire': 0,
                    'message': 'No hires in this time period'
                }
            
            # Calculate average time to hire
            time_to_hire_days = []
            for app in hired_applications:
                days_to_hire = (app.updated_at - app.created_at).days
                time_to_hire_days.append(days_to_hire)
            
            avg_time_to_hire = sum(time_to_hire_days) / len(time_to_hire_days)
            
            # Calculate cost per hire
            # Factors: platform fees, advertising, recruiter time, interview costs
            platform_fee_per_job = 100  # Assume $100 per job posting
            avg_interview_cost = 150  # Estimated cost per interview
            avg_screening_cost = 50  # Cost of screening per candidate
            
            total_jobs = Job.query.filter(
                Job.employer_id == employer_id,
                Job.created_at >= cutoff_date
            ).count()
            
            total_applications = JobApplication.query.join(Job).filter(
                Job.employer_id == employer_id,
                JobApplication.created_at >= cutoff_date
            ).count()
            
            interviews_conducted = JobApplication.query.join(Job).filter(
                Job.employer_id == employer_id,
                JobApplication.status.in_(['interview', 'offer', 'accepted']),
                JobApplication.created_at >= cutoff_date
            ).count()
            
            # Total recruiting costs
            platform_costs = total_jobs * platform_fee_per_job
            screening_costs = total_applications * avg_screening_cost
            interview_costs = interviews_conducted * avg_interview_cost
            
            total_recruiting_cost = platform_costs + screening_costs + interview_costs
            cost_per_hire = total_recruiting_cost / total_hires if total_hires > 0 else 0
            
            # Quality of hire metrics
            # Based on time to productivity, hiring manager satisfaction (simulated for now)
            quality_scores = []
            for app in hired_applications:
                candidate = User.query.get(app.user_id)
                if candidate:
                    # Quality score based on: GPA, experience, skills match
                    score = 5.0  # Base score
                    
                    # GPA bonus (if available)
                    if hasattr(candidate, 'gpa') and candidate.gpa:
                        score += min(candidate.gpa / 4.0 * 2, 2)  # Up to +2 points
                    
                    # Experience bonus
                    if hasattr(candidate, 'years_experience') and candidate.years_experience:
                        score += min(candidate.years_experience * 0.3, 2)  # Up to +2 points
                    
                    # Application strength (cover letter, resume)
                    if app.cover_letter and len(app.cover_letter) > 200:
                        score += 0.5
                    
                    quality_scores.append(min(score, 10.0))  # Cap at 10
            
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 7.0
            
            # ROI calculation
            # Assume average value of a hire is $50,000 first year contribution
            avg_hire_value = 50000
            total_hire_value = avg_hire_value * total_hires
            roi_percentage = ((total_hire_value - total_recruiting_cost) / total_recruiting_cost * 100) if total_recruiting_cost > 0 else 0
            
            # Offer acceptance rate
            offers_made = JobApplication.query.join(Job).filter(
                Job.employer_id == employer_id,
                JobApplication.status.in_(['offer', 'accepted']),
                JobApplication.created_at >= cutoff_date
            ).count()
            
            offer_acceptance_rate = (total_hires / offers_made * 100) if offers_made > 0 else 0
            
            logger.info(f"Calculated ROI for employer {employer_id}: ${cost_per_hire:.2f} per hire, {avg_time_to_hire:.1f} days")
            
            return {
                'success': True,
                'total_hires': total_hires,
                'cost_per_hire': round(cost_per_hire, 2),
                'average_time_to_hire': round(avg_time_to_hire, 1),
                'fastest_hire_days': min(time_to_hire_days) if time_to_hire_days else 0,
                'slowest_hire_days': max(time_to_hire_days) if time_to_hire_days else 0,
                'quality_of_hire_score': round(avg_quality_score, 1),
                'total_recruiting_cost': round(total_recruiting_cost, 2),
                'roi_percentage': round(roi_percentage, 1),
                'offer_acceptance_rate': round(offer_acceptance_rate, 1),
                'breakdown': {
                    'platform_costs': round(platform_costs, 2),
                    'screening_costs': round(screening_costs, 2),
                    'interview_costs': round(interview_costs, 2)
                },
                'time_period_days': time_period
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_source_effectiveness(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Track which sources/channels bring the best candidates
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back
            
        Returns:
            Dictionary with source performance metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get all applications for this employer's jobs
            applications = db.session.query(
                JobApplication,
                Job,
                User
            ).join(Job, JobApplication.job_id == Job.id).join(
                User, JobApplication.user_id == User.id
            ).filter(
                Job.employer_id == employer_id,
                JobApplication.created_at >= cutoff_date
            ).all()
            
            # Track sources (where candidates came from)
            from typing import TypedDict
            class SourceStat(TypedDict):
                total_applications: int
                hired: int
                interviews: int
                avg_quality: list
                avg_time_to_hire: list
            
            source_stats: dict = defaultdict(lambda: {
                'total_applications': 0,
                'hired': 0,
                'interviews': 0,
                'avg_quality': [],
                'avg_time_to_hire': []
            })
            
            for app, job, user in applications:
                # Determine source
                source = 'Direct' if not hasattr(app, 'source') else app.source or 'Direct'
                
                # Could also be: Email Campaign, Career Fair, Referral, Social Media, etc.
                # For now, we'll use referral info if available
                if hasattr(user, 'referred_by') and user.referred_by:
                    source = 'Referral'
                elif hasattr(app, 'application_source'):
                    source = app.application_source
                
                source_stats[source]['total_applications'] += 1
                
                # Track hires
                if app.status == 'accepted':
                    source_stats[source]['hired'] += 1
                    days_to_hire = (app.updated_at - app.created_at).days
                    source_stats[source]['avg_time_to_hire'].append(days_to_hire)
                
                # Track interviews
                if app.status in ['interview', 'offer', 'accepted']:
                    source_stats[source]['interviews'] += 1
                
                # Quality score (based on candidate profile)
                quality = 5.0
                if hasattr(user, 'gpa') and user.gpa:
                    quality += min(user.gpa / 4.0 * 2, 2)
                if hasattr(user, 'years_experience') and user.years_experience:
                    quality += min(user.years_experience * 0.3, 2)
                source_stats[source]['avg_quality'].append(min(quality, 10.0))
            
            # Calculate metrics for each source
            source_performance = []
            for source, stats in source_stats.items():
                total_apps = int(stats['total_applications'])
                hired = int(stats['hired'])
                interviews = int(stats['interviews'])
                
                hire_rate = (hired / total_apps * 100) if total_apps > 0 else 0
                interview_rate = (interviews / total_apps * 100) if total_apps > 0 else 0
                avg_quality = sum(stats['avg_quality']) / len(stats['avg_quality']) if stats['avg_quality'] else 0
                avg_time = sum(stats['avg_time_to_hire']) / len(stats['avg_time_to_hire']) if stats['avg_time_to_hire'] else 0
                
                source_performance.append({
                    'source': source,
                    'total_applications': total_apps,
                    'hires': hired,
                    'hire_rate': round(hire_rate, 1),
                    'interview_rate': round(interview_rate, 1),
                    'avg_candidate_quality': round(avg_quality, 1),
                    'avg_time_to_hire_days': round(avg_time, 1) if avg_time > 0 else None
                })
            
            # Sort by hire rate
            source_performance.sort(key=lambda x: x['hire_rate'], reverse=True)
            
            # Recommendations
            recommendations = []
            if source_performance:
                best_source = source_performance[0]
                recommendations.append(f"Focus on {best_source['source']} - highest hire rate at {best_source['hire_rate']}%")
                
                if len(source_performance) > 1:
                    worst_source = source_performance[-1]
                    if worst_source['hire_rate'] < 5:
                        recommendations.append(f"Consider reducing spend on {worst_source['source']} - low hire rate")
            
            logger.info(f"Generated source effectiveness for employer {employer_id}: {len(source_performance)} sources tracked")
            
            return {
                'success': True,
                'sources': source_performance,
                'recommendations': recommendations,
                'time_period_days': time_period
            }
            
        except Exception as e:
            logger.error(f"Error getting source effectiveness for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_diversity_metrics(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Track diversity and inclusion metrics (EEOC compliant)
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back
            
        Returns:
            Dictionary with diversity metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get all applications and hires
            applications = db.session.query(
                JobApplication,
                Job,
                User
            ).join(Job, JobApplication.job_id == Job.id).join(
                User, JobApplication.user_id == User.id
            ).filter(
                Job.employer_id == employer_id,
                JobApplication.created_at >= cutoff_date
            ).all()
            
            hires = [app for app, job, user in applications if app[0].status == 'accepted']
            
            # Gender diversity
            gender_stats = {
                'applicants': defaultdict(int),
                'hires': defaultdict(int)
            }
            
            # Ethnicity diversity (if provided)
            ethnicity_stats = {
                'applicants': defaultdict(int),
                'hires': defaultdict(int)
            }
            
            # Disability status
            disability_stats = {
                'applicants': defaultdict(int),
                'hires': defaultdict(int)
            }
            
            # Veteran status
            veteran_stats = {
                'applicants': defaultdict(int),
                'hires': defaultdict(int)
            }
            
            for app, job, user in applications:
                # Gender
                gender = getattr(user, 'gender', 'Not Specified') or 'Not Specified'
                gender_stats['applicants'][gender] += 1
                if app.status == 'accepted':
                    gender_stats['hires'][gender] += 1
                
                # Ethnicity
                ethnicity = getattr(user, 'ethnicity', 'Not Specified') or 'Not Specified'
                ethnicity_stats['applicants'][ethnicity] += 1
                if app.status == 'accepted':
                    ethnicity_stats['hires'][ethnicity] += 1
                
                # Disability
                has_disability = getattr(user, 'has_disability', False)
                disability_key = 'Yes' if has_disability else 'No'
                disability_stats['applicants'][disability_key] += 1
                if app.status == 'accepted':
                    disability_stats['hires'][disability_key] += 1
                
                # Veteran
                is_veteran = getattr(user, 'is_veteran', False)
                veteran_key = 'Yes' if is_veteran else 'No'
                veteran_stats['applicants'][veteran_key] += 1
                if app.status == 'accepted':
                    veteran_stats['hires'][veteran_key] += 1
            
            # Calculate percentages
            total_applicants = len(applications)
            total_hires = len(hires)
            
            diversity_summary = {
                'gender': {
                    'applicants': dict(gender_stats['applicants']),
                    'hires': dict(gender_stats['hires']),
                    'applicant_percentages': {k: round(v/total_applicants*100, 1) for k, v in gender_stats['applicants'].items()},
                    'hire_percentages': {k: round(v/total_hires*100, 1) for k, v in gender_stats['hires'].items()} if total_hires > 0 else {}
                },
                'ethnicity': {
                    'applicants': dict(ethnicity_stats['applicants']),
                    'hires': dict(ethnicity_stats['hires']),
                    'applicant_percentages': {k: round(v/total_applicants*100, 1) for k, v in ethnicity_stats['applicants'].items()},
                    'hire_percentages': {k: round(v/total_hires*100, 1) for k, v in ethnicity_stats['hires'].items()} if total_hires > 0 else {}
                },
                'disability': {
                    'applicants': dict(disability_stats['applicants']),
                    'hires': dict(disability_stats['hires']),
                    'applicant_percentages': {k: round(v/total_applicants*100, 1) for k, v in disability_stats['applicants'].items()},
                    'hire_percentages': {k: round(v/total_hires*100, 1) for k, v in disability_stats['hires'].items()} if total_hires > 0 else {}
                },
                'veteran': {
                    'applicants': dict(veteran_stats['applicants']),
                    'hires': dict(veteran_stats['hires']),
                    'applicant_percentages': {k: round(v/total_applicants*100, 1) for k, v in veteran_stats['applicants'].items()},
                    'hire_percentages': {k: round(v/total_hires*100, 1) for k, v in veteran_stats['hires'].items()} if total_hires > 0 else {}
                }
            }
            
            # Insights
            insights = []
            
            # Check for gender balance
            if 'Female' in gender_stats['hires'] and total_hires > 0:
                female_hire_pct = gender_stats['hires']['Female'] / total_hires * 100
                if female_hire_pct < 30:
                    insights.append("Consider expanding outreach to increase gender diversity")
                elif female_hire_pct > 45:
                    insights.append("Strong gender diversity in hires")
            
            # Check for disability inclusion
            if 'Yes' in disability_stats['hires'] and total_hires > 0:
                disability_hire_pct = disability_stats['hires']['Yes'] / total_hires * 100
                if disability_hire_pct > 5:
                    insights.append("Excellent disability inclusion - above national average")
            
            logger.info(f"Generated diversity metrics for employer {employer_id}: {total_applicants} applicants, {total_hires} hires")
            
            return {
                'success': True,
                'diversity_summary': diversity_summary,
                'total_applicants': total_applicants,
                'total_hires': total_hires,
                'insights': insights,
                'time_period_days': time_period,
                'note': 'All data is anonymized and EEOC compliant'
            }
            
        except Exception as e:
            logger.error(f"Error getting diversity metrics for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def benchmark_against_industry(employer_id: int, industry: str = None, time_period: int = 90) -> Dict[str, Any]:
        """
        Compare employer's metrics against industry benchmarks
        
        Args:
            employer_id: ID of the employer
            industry: Industry category (Technology, Healthcare, etc.)
            time_period: Days to look back
            
        Returns:
            Dictionary with comparisons to industry standards
        """
        try:
            # Get employer's company industry
            employer = User.query.get(employer_id)
            if not employer or not employer.company_id:
                return {'success': False, 'error': 'Employer not found'}
            
            company = Company.query.get(employer.company_id)
            detected_industry = industry or getattr(company, 'industry', 'Other') or 'Other'
            
            # Get employer's actual metrics
            roi_data = EmployerAnalyticsService.calculate_roi(employer_id, time_period)
            pipeline_data = EmployerAnalyticsService.generate_pipeline_metrics(employer_id, time_period)
            
            if not roi_data.get('success') or not pipeline_data.get('success'):
                return {'success': False, 'error': 'Could not fetch employer metrics'}
            
            # Get industry benchmarks
            benchmarks = EmployerAnalyticsService.INDUSTRY_BENCHMARKS
            
            # Compare metrics
            comparisons = []
            
            # Time to hire comparison
            employer_time_to_hire = roi_data.get('average_time_to_hire', 0)
            industry_time_to_hire = benchmarks['time_to_hire_days'].get(detected_industry, 40)
            time_diff = employer_time_to_hire - industry_time_to_hire
            time_status = 'faster' if time_diff < 0 else 'slower'
            
            comparisons.append({
                'metric': 'Time to Hire',
                'employer_value': employer_time_to_hire,
                'industry_average': industry_time_to_hire,
                'difference': abs(time_diff),
                'status': time_status,
                'unit': 'days',
                'insight': f"You are hiring {abs(time_diff):.0f} days {time_status} than industry average"
            })
            
            # Cost per hire comparison
            employer_cost_per_hire = roi_data.get('cost_per_hire', 0)
            industry_cost_per_hire = benchmarks['cost_per_hire'].get(detected_industry, 4000)
            cost_diff = employer_cost_per_hire - industry_cost_per_hire
            cost_status = 'lower' if cost_diff < 0 else 'higher'
            
            comparisons.append({
                'metric': 'Cost per Hire',
                'employer_value': employer_cost_per_hire,
                'industry_average': industry_cost_per_hire,
                'difference': abs(cost_diff),
                'status': cost_status,
                'unit': 'USD',
                'insight': f"Your cost is ${abs(cost_diff):.0f} {cost_status} than industry average"
            })
            
            # Offer acceptance rate comparison
            employer_acceptance_rate = roi_data.get('offer_acceptance_rate', 0) / 100
            industry_acceptance_rate = benchmarks['offer_acceptance_rate'].get(detected_industry, 0.85)
            acceptance_diff = employer_acceptance_rate - industry_acceptance_rate
            acceptance_status = 'higher' if acceptance_diff > 0 else 'lower'
            
            comparisons.append({
                'metric': 'Offer Acceptance Rate',
                'employer_value': employer_acceptance_rate * 100,
                'industry_average': industry_acceptance_rate * 100,
                'difference': abs(acceptance_diff) * 100,
                'status': acceptance_status,
                'unit': 'percent',
                'insight': f"Your acceptance rate is {abs(acceptance_diff)*100:.1f}% {acceptance_status} than industry"
            })
            
            # Quality of hire comparison
            employer_quality = roi_data.get('quality_of_hire_score', 0)
            industry_quality = benchmarks['candidate_quality_score'].get(detected_industry, 7.5)
            quality_diff = employer_quality - industry_quality
            quality_status = 'higher' if quality_diff > 0 else 'lower'
            
            comparisons.append({
                'metric': 'Candidate Quality Score',
                'employer_value': employer_quality,
                'industry_average': industry_quality,
                'difference': abs(quality_diff),
                'status': quality_status,
                'unit': 'score',
                'insight': f"Your candidates score {abs(quality_diff):.1f} points {quality_status} than industry average"
            })
            
            # Overall performance rating
            performance_score = 0
            if time_status == 'faster':
                performance_score += 25
            if cost_status == 'lower':
                performance_score += 25
            if acceptance_status == 'higher':
                performance_score += 25
            if quality_status == 'higher':
                performance_score += 25
            
            performance_rating = 'Excellent' if performance_score >= 75 else 'Good' if performance_score >= 50 else 'Average' if performance_score >= 25 else 'Needs Improvement'
            
            # Recommendations
            recommendations = []
            if time_status == 'slower':
                recommendations.append("Streamline your interview process to reduce time to hire")
            if cost_status == 'higher':
                recommendations.append("Consider optimizing your recruiting spend and focusing on high-ROI channels")
            if acceptance_status == 'lower':
                recommendations.append("Improve offer competitiveness or employer branding to increase acceptance rates")
            if quality_status == 'lower':
                recommendations.append("Refine job descriptions and screening criteria to attract higher quality candidates")
            
            if not recommendations:
                recommendations.append("Excellent performance! Continue current strategies and look for incremental improvements")
            
            logger.info(f"Generated benchmark comparison for employer {employer_id}: {performance_rating} performance")
            
            return {
                'success': True,
                'industry': detected_industry,
                'comparisons': comparisons,
                'performance_score': performance_score,
                'performance_rating': performance_rating,
                'recommendations': recommendations,
                'time_period_days': time_period
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def predict_hiring_needs(employer_id: int, forecast_months: int = 6) -> Dict[str, Any]:
        """
        Use ML to predict future hiring needs based on historical patterns
        
        Args:
            employer_id: ID of the employer
            forecast_months: Number of months to forecast
            
        Returns:
            Dictionary with hiring predictions
        """
        try:
            # Get historical hiring data (last 12 months)
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            
            # Get monthly hire counts
            monthly_hires = db.session.query(
                extract('year', JobApplication.updated_at).label('year'),
                extract('month', JobApplication.updated_at).label('month'),
                func.count(JobApplication.id).label('hire_count')
            ).join(Job, JobApplication.job_id == Job.id).filter(
                Job.employer_id == employer_id,
                JobApplication.status == 'accepted',
                JobApplication.updated_at >= one_year_ago
            ).group_by('year', 'month').order_by('year', 'month').all()
            
            if len(monthly_hires) < 3:
                return {
                    'success': True,
                    'forecast': [],
                    'message': 'Insufficient historical data for prediction (need at least 3 months)'
                }
            
            # Simple moving average forecast
            hire_counts = [h.hire_count for h in monthly_hires]
            avg_hires_per_month = sum(hire_counts) / len(hire_counts)
            
            # Detect trend (increasing, decreasing, stable)
            if len(hire_counts) >= 6:
                first_half_avg = sum(hire_counts[:len(hire_counts)//2]) / (len(hire_counts)//2)
                second_half_avg = sum(hire_counts[len(hire_counts)//2:]) / (len(hire_counts) - len(hire_counts)//2)
                trend_direction = 'increasing' if second_half_avg > first_half_avg * 1.1 else 'decreasing' if second_half_avg < first_half_avg * 0.9 else 'stable'
                trend_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
            else:
                trend_direction = 'stable'
                trend_rate = 0
            
            # Generate forecast
            forecast = []
            current_date = datetime.utcnow()
            
            for i in range(forecast_months):
                forecast_date = current_date + timedelta(days=30 * (i + 1))
                
                # Apply trend to forecast
                if trend_direction == 'increasing':
                    predicted_hires = avg_hires_per_month * (1 + (trend_rate / 12) * (i + 1))
                elif trend_direction == 'decreasing':
                    predicted_hires = max(0, avg_hires_per_month * (1 + (trend_rate / 12) * (i + 1)))
                else:
                    predicted_hires = avg_hires_per_month
                
                forecast.append({
                    'month': forecast_date.strftime('%B %Y'),
                    'predicted_hires': round(predicted_hires, 1),
                    'confidence': 'medium' if i < 3 else 'low'  # Confidence decreases over time
                })
            
            # Calculate recommended budget
            roi_data = EmployerAnalyticsService.calculate_roi(employer_id, 90)
            cost_per_hire = roi_data.get('cost_per_hire', 4000)
            
            total_predicted_hires = sum(f['predicted_hires'] for f in forecast)
            recommended_budget = total_predicted_hires * cost_per_hire
            
            # Insights
            insights = []
            insights.append(f"Historical average: {avg_hires_per_month:.1f} hires per month")
            insights.append(f"Hiring trend: {trend_direction}")
            insights.append(f"Predicted total hires in next {forecast_months} months: {total_predicted_hires:.0f}")
            insights.append(f"Recommended recruiting budget: ${recommended_budget:,.0f}")
            
            if trend_direction == 'increasing':
                insights.append("Consider increasing recruiting capacity to handle growing hiring needs")
            elif trend_direction == 'decreasing':
                insights.append("Hiring demand is decreasing - consider optimizing recruiting spend")
            
            logger.info(f"Generated hiring forecast for employer {employer_id}: {total_predicted_hires:.0f} predicted hires over {forecast_months} months")
            
            return {
                'success': True,
                'forecast': forecast,
                'historical_average': round(avg_hires_per_month, 1),
                'trend': trend_direction,
                'total_predicted_hires': round(total_predicted_hires, 1),
                'recommended_budget': round(recommended_budget, 2),
                'insights': insights,
                'forecast_months': forecast_months
            }
            
        except Exception as e:
            logger.error(f"Error predicting hiring needs for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_candidate_engagement_metrics(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Track how candidates engage with employer's content
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back
            
        Returns:
            Dictionary with engagement metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get employer's company
            employer = User.query.get(employer_id)
            if not employer or not employer.company_id:
                return {'success': False, 'error': 'Employer not found'}
            
            company = Company.query.get(employer.company_id)
            
            # Job views
            total_job_views = db.session.query(
                func.sum(Job.view_count)
            ).filter(
                Job.employer_id == employer_id,
                Job.created_at >= cutoff_date
            ).scalar() or 0
            
            # Applications
            total_applications = JobApplication.query.join(Job).filter(
                Job.employer_id == employer_id,
                JobApplication.created_at >= cutoff_date
            ).count()
            
            # Company page views (if tracked)
            company_views = getattr(company, 'view_count', 0)
            
            # Event attendance (if employer hosted events)
            event_attendance = db.session.query(
                func.count(EventAttendee.id)
            ).join(Event, EventAttendee.event_id == Event.id).filter(
                Event.organizer_id == employer_id,
                Event.start_time >= cutoff_date
            ).scalar() or 0
            
            # Messages received
            messages_received = Message.query.filter(
                Message.recipient_id == employer_id,
                Message.created_at >= cutoff_date
            ).count()
            
            # Calculate engagement rate
            engagement_rate = (total_applications / total_job_views * 100) if total_job_views > 0 else 0
            
            # Top performing jobs by engagement
            top_jobs = db.session.query(
                Job.id,
                Job.title,
                Job.view_count,
                func.count(JobApplication.id).label('app_count'),
                (func.count(JobApplication.id).cast(db.Float) / Job.view_count * 100).label('conversion_rate')
            ).outerjoin(JobApplication, Job.id == JobApplication.job_id).filter(
                Job.employer_id == employer_id,
                Job.created_at >= cutoff_date,
                Job.view_count > 0
            ).group_by(Job.id, Job.title, Job.view_count).order_by(
                'conversion_rate DESC'
            ).limit(5).all()
            
            top_jobs_data = [
                {
                    'job_id': job.id,
                    'title': job.title,
                    'views': job.view_count,
                    'applications': job.app_count,
                    'conversion_rate': round(job.conversion_rate, 1)
                }
                for job in top_jobs
            ]
            
            logger.info(f"Generated engagement metrics for employer {employer_id}: {total_applications} applications, {engagement_rate:.1f}% engagement rate")
            
            return {
                'success': True,
                'total_job_views': total_job_views,
                'total_applications': total_applications,
                'engagement_rate': round(engagement_rate, 2),
                'company_page_views': company_views,
                'event_attendance': event_attendance,
                'messages_received': messages_received,
                'top_performing_jobs': top_jobs_data,
                'time_period_days': time_period
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement metrics for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def generate_comprehensive_report(employer_id: int, time_period: int = 90) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report combining all metrics
        
        Args:
            employer_id: ID of the employer
            time_period: Days to look back
            
        Returns:
            Dictionary with complete analytics report
        """
        try:
            # Get employer info
            employer = User.query.get(employer_id)
            if not employer:
                return {'success': False, 'error': 'Employer not found'}
            
            # Gather all analytics
            pipeline = EmployerAnalyticsService.generate_pipeline_metrics(employer_id, time_period)
            roi = EmployerAnalyticsService.calculate_roi(employer_id, time_period)
            sources = EmployerAnalyticsService.get_source_effectiveness(employer_id, time_period)
            diversity = EmployerAnalyticsService.get_diversity_metrics(employer_id, time_period)
            industry = employer.company.industry if employer.company else 'Other'
            benchmarks = EmployerAnalyticsService.benchmark_against_industry(employer_id, industry, time_period)
            forecast = EmployerAnalyticsService.predict_hiring_needs(employer_id, 6)
            engagement = EmployerAnalyticsService.get_candidate_engagement_metrics(employer_id, time_period)
            
            # Generate executive summary
            executive_summary = {
                'report_period': f'{time_period} days',
                'generated_at': datetime.utcnow().isoformat(),
                'employer_name': employer.full_name or employer.email,
                'company_name': employer.company.name if employer.company else 'N/A',
                'key_metrics': {
                    'total_applications': pipeline.get('total_candidates', 0),
                    'total_hires': pipeline.get('total_hires', 0),
                    'cost_per_hire': roi.get('cost_per_hire', 0),
                    'time_to_hire': roi.get('average_time_to_hire', 0),
                    'engagement_rate': engagement.get('engagement_rate', 0),
                    'performance_rating': benchmarks.get('performance_rating', 'N/A')
                },
                'top_insights': []
            }
            
            # Add top insights
            if roi.get('roi_percentage', 0) > 1000:
                executive_summary['top_insights'].append('Excellent ROI on recruiting investment')
            
            if pipeline.get('conversion_rates', {}).get('overall_hire_rate', 0) > 10:
                executive_summary['top_insights'].append('Strong conversion rate from applications to hires')
            
            if benchmarks.get('performance_score', 0) >= 75:
                executive_summary['top_insights'].append('Performing above industry benchmarks across key metrics')
            
            logger.info(f"Generated comprehensive report for employer {employer_id}")
            
            return {
                'success': True,
                'executive_summary': executive_summary,
                'pipeline_metrics': pipeline,
                'roi_metrics': roi,
                'source_effectiveness': sources,
                'diversity_metrics': diversity,
                'industry_benchmarks': benchmarks,
                'hiring_forecast': forecast,
                'engagement_metrics': engagement
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report for employer {employer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
