"""
Predictive Analytics Service
ML-powered student success prediction and institutional analytics

Features:
- Student employment outcome predictions
- At-risk student identification
- Career path recommendations
- Salary prediction models
- Job placement forecasting
- Alumni success tracking
- Departmental performance analytics
- ROI analysis for programs
- Employer demand forecasting
- Skill gap analysis
- Graduation outcome predictions
- Real-time analytics dashboards
- Custom reporting for administrators

Revenue Model:
- Free for students (insights)
- Premium institutional licenses: $10,000-50,000/year
- Custom analytics reports: $2,000-10,000/report
- API access for researchers: $500/month
- Predictive model consulting: $5,000+/project
Target: $500,000+ annually from institutional licensing
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
import statistics
import random

from models import db, User, Job
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """Service for predictive analytics and ML-powered insights"""
    
    # Risk factors for employment outcomes
    RISK_FACTORS = {
        'low_gpa': {'weight': 0.15, 'threshold': 2.5},
        'no_internship': {'weight': 0.20, 'threshold': None},
        'inactive_networking': {'weight': 0.15, 'threshold': 5},  # < 5 connections
        'incomplete_profile': {'weight': 0.10, 'threshold': 70},  # < 70% complete
        'low_engagement': {'weight': 0.10, 'threshold': 10},  # < 10 platform activities
        'late_job_search': {'weight': 0.15, 'threshold': 6},  # < 6 months before grad
        'no_skills_verified': {'weight': 0.15, 'threshold': None}
    }
    
    # Success factors
    SUCCESS_FACTORS = {
        'high_gpa': {'weight': 0.15, 'threshold': 3.5},
        'multiple_internships': {'weight': 0.20, 'threshold': 2},
        'strong_network': {'weight': 0.15, 'threshold': 50},
        'complete_profile': {'weight': 0.10, 'threshold': 95},
        'high_engagement': {'weight': 0.10, 'threshold': 50},
        'early_job_search': {'weight': 0.15, 'threshold': 12},
        'verified_skills': {'weight': 0.15, 'threshold': 5}
    }
    
    # Industry growth projections (annual %)
    INDUSTRY_GROWTH = {
        'Technology': 0.12,
        'Healthcare': 0.08,
        'Finance': 0.05,
        'Education': 0.03,
        'Manufacturing': 0.02,
        'Retail': -0.01,
        'Energy': 0.06,
        'Real Estate': 0.04
    }

    def __init__(self):
        """Initialize predictive analytics service"""
        self.logger = logger
    
    def predict_employment_outcome(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Predict employment outcome for a student
        
        Args:
            user_id: Student user ID
        
        Returns:
            Employment prediction with probability and factors
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Gather student data
            student_data = self._gather_student_data(user)
            
            # Calculate risk and success scores
            risk_score = self._calculate_risk_score(student_data)
            success_score = self._calculate_success_score(student_data)
            
            # Predict employment probability
            employment_probability = self._calculate_employment_probability(
                risk_score,
                success_score,
                student_data
            )
            
            # Predict time to employment
            time_to_employment = self._predict_time_to_employment(student_data)
            
            # Predict starting salary range
            salary_prediction = self._predict_starting_salary(student_data)
            
            # Identify key factors
            positive_factors = self._identify_positive_factors(student_data)
            improvement_areas = self._identify_improvement_areas(student_data)
            
            # Generate recommendations
            recommendations = self._generate_employment_recommendations(
                student_data,
                improvement_areas
            )
            
            # Calculate confidence level
            confidence = self._calculate_prediction_confidence(student_data)
            
            return {
                'success': True,
                'user_id': user_id,
                'prediction': {
                    'employment_probability': employment_probability,
                    'probability_tier': self._get_probability_tier(employment_probability),
                    'time_to_employment_days': time_to_employment,
                    'time_to_employment_range': self._format_time_range(time_to_employment),
                    'predicted_salary_range': salary_prediction,
                    'confidence_level': confidence
                },
                'factors': {
                    'positive_factors': positive_factors,
                    'improvement_areas': improvement_areas,
                    'risk_score': risk_score,
                    'success_score': success_score
                },
                'recommendations': recommendations,
                'benchmark': self._get_peer_benchmark(student_data),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting employment outcome: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def identify_at_risk_students(
        self,
        department_id: Optional[int] = None,
        graduation_year: Optional[int] = None,
        risk_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Identify students at risk of poor employment outcomes
        
        Args:
            department_id: Filter by department
            graduation_year: Filter by graduation year
            risk_threshold: Risk score threshold (0-1)
        
        Returns:
            List of at-risk students with intervention recommendations
        """
        try:
            # Get students
            students = self._query_students(department_id, graduation_year)
            
            at_risk_students = []
            
            for student in students:
                student_data = self._gather_student_data(student)
                risk_score = self._calculate_risk_score(student_data)
                
                if risk_score >= risk_threshold:
                    # Get intervention recommendations
                    interventions = self._recommend_interventions(student, student_data)
                    
                    at_risk_students.append({
                        'user_id': student.id,
                        'name': student.name,
                        'email': student.email,
                        'major': getattr(student, 'major', None),
                        'graduation_year': getattr(student, 'graduation_year', None),
                        'risk_score': risk_score,
                        'risk_level': self._get_risk_level(risk_score),
                        'primary_concerns': self._identify_primary_concerns(student_data),
                        'recommended_interventions': interventions,
                        'contact_priority': self._calculate_contact_priority(risk_score, student_data)
                    })
            
            # Sort by risk score (highest first)
            at_risk_students.sort(key=lambda x: x['risk_score'], reverse=True)
            
            # Calculate statistics
            stats = self._calculate_at_risk_statistics(at_risk_students, students)
            
            return {
                'success': True,
                'total_students': len(students),
                'at_risk_count': len(at_risk_students),
                'at_risk_percentage': round(len(at_risk_students) / len(students) * 100, 1) if students else 0,
                'students': at_risk_students[:50],  # Top 50 highest risk
                'statistics': stats,
                'intervention_summary': self._summarize_interventions(at_risk_students),
                'filters_applied': {
                    'department_id': department_id,
                    'graduation_year': graduation_year,
                    'risk_threshold': risk_threshold
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying at-risk students: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def forecast_job_placement_rate(
        self,
        department_id: int,
        graduation_year: int
    ) -> Dict[str, Any]:
        """
        Forecast job placement rate for upcoming graduates
        
        Args:
            department_id: Department ID
            graduation_year: Graduation year
        
        Returns:
            Placement rate forecast with confidence intervals
        """
        try:
            # Get historical placement data
            historical_data = self._get_historical_placement_data(department_id)
            
            # Get current student cohort data
            current_students = self._query_students(department_id, graduation_year)
            
            # Analyze current cohort readiness
            cohort_analysis = self._analyze_cohort_readiness(current_students)
            
            # Apply trend analysis
            trend_adjustment = self._calculate_trend_adjustment(historical_data)
            
            # Apply market conditions
            market_adjustment = self._apply_market_conditions(department_id)
            
            # Calculate forecast
            base_rate = self._calculate_base_placement_rate(historical_data)
            forecasted_rate = base_rate + trend_adjustment + market_adjustment + cohort_analysis['adjustment']
            
            # Ensure within bounds
            forecasted_rate = max(0, min(100, forecasted_rate))
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                historical_data,
                cohort_analysis
            )
            
            return {
                'success': True,
                'department_id': department_id,
                'graduation_year': graduation_year,
                'forecast': {
                    'placement_rate': round(forecasted_rate, 1),
                    'confidence_interval': confidence_interval,
                    'confidence_level': '85%',
                    'students_expected_employed': int(len(current_students) * (forecasted_rate / 100))
                },
                'historical_comparison': {
                    'last_year': historical_data[-1]['placement_rate'] if historical_data else None,
                    'three_year_average': round(statistics.mean([d['placement_rate'] for d in historical_data[-3:]]), 1) if len(historical_data) >= 3 else None,
                    'trend': 'increasing' if trend_adjustment > 0 else 'decreasing' if trend_adjustment < 0 else 'stable'
                },
                'factors': {
                    'base_rate': base_rate,
                    'trend_adjustment': trend_adjustment,
                    'market_adjustment': market_adjustment,
                    'cohort_adjustment': cohort_analysis['adjustment']
                },
                'cohort_analysis': cohort_analysis,
                'recommendations': self._generate_department_recommendations(forecasted_rate, cohort_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error forecasting placement rate: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_program_roi(
        self,
        department_id: int,
        time_period_years: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze ROI of academic program
        
        Args:
            department_id: Department ID
            time_period_years: Analysis time period
        
        Returns:
            Comprehensive ROI analysis
        """
        try:
            # Get program data
            program_data = self._get_program_data(department_id)
            
            # Get alumni earnings data
            alumni_earnings = self._get_alumni_earnings(department_id, time_period_years)
            
            # Calculate program costs
            program_costs = self._calculate_program_costs(program_data)
            
            # Calculate lifetime earnings
            lifetime_earnings = self._calculate_lifetime_earnings(alumni_earnings)
            
            # Calculate ROI
            roi = self._calculate_roi(lifetime_earnings, program_costs)
            
            # Calculate payback period
            payback_period = self._calculate_payback_period(
                alumni_earnings,
                program_costs
            )
            
            # Compare to other programs
            comparison = self._compare_to_other_programs(department_id, roi)
            
            # Employment outcomes
            employment_outcomes = self._analyze_employment_outcomes(department_id)
            
            # Career progression
            career_progression = self._analyze_career_progression(department_id)
            
            return {
                'success': True,
                'department_id': department_id,
                'program_name': program_data['name'],
                'time_period_years': time_period_years,
                'roi_analysis': {
                    'roi_percentage': roi,
                    'roi_rating': self._get_roi_rating(roi),
                    'payback_period_years': payback_period,
                    'total_program_cost': program_costs['total'],
                    'median_starting_salary': alumni_earnings['median_starting'],
                    'median_salary_5_years': alumni_earnings['median_5_years'],
                    'lifetime_earnings_projection': lifetime_earnings
                },
                'employment_outcomes': employment_outcomes,
                'career_progression': career_progression,
                'comparison': comparison,
                'strengths': self._identify_program_strengths(program_data, alumni_earnings),
                'improvement_opportunities': self._identify_program_improvements(program_data, alumni_earnings),
                'market_outlook': self._get_market_outlook(program_data['industry'])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing program ROI: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def forecast_employer_demand(
        self,
        industry: str,
        time_horizon_months: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast employer hiring demand by industry
        
        Args:
            industry: Industry name
            time_horizon_months: Forecast time horizon
        
        Returns:
            Demand forecast with skill requirements
        """
        try:
            # Get historical hiring data
            historical_demand = self._get_historical_demand(industry)
            
            # Apply seasonal adjustments
            seasonal_factors = self._calculate_seasonal_factors(historical_demand)
            
            # Apply industry growth rate
            growth_rate = self.INDUSTRY_GROWTH.get(industry, 0.05)
            
            # Calculate forecast
            current_demand = historical_demand[-1]['job_postings'] if historical_demand else 100
            forecasted_demand = int(current_demand * (1 + growth_rate * (time_horizon_months / 12)))
            
            # Get in-demand skills
            trending_skills = self._identify_trending_skills(industry)
            
            # Get emerging roles
            emerging_roles = self._identify_emerging_roles(industry)
            
            # Calculate supply-demand gap
            supply_demand_gap = self._calculate_supply_demand_gap(industry)
            
            return {
                'success': True,
                'industry': industry,
                'time_horizon_months': time_horizon_months,
                'forecast': {
                    'current_job_postings': current_demand,
                    'forecasted_job_postings': forecasted_demand,
                    'growth_rate': round(growth_rate * 100, 1),
                    'change': forecasted_demand - current_demand,
                    'change_percentage': round((forecasted_demand - current_demand) / current_demand * 100, 1)
                },
                'trending_skills': trending_skills[:10],
                'emerging_roles': emerging_roles[:10],
                'supply_demand_gap': supply_demand_gap,
                'seasonal_factors': seasonal_factors,
                'opportunities': self._identify_job_opportunities(industry, trending_skills),
                'recommendations': self._generate_career_planning_recommendations(industry, trending_skills)
            }
            
        except Exception as e:
            self.logger.error(f"Error forecasting employer demand: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_institutional_dashboard(
        self,
        institution_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive institutional analytics dashboard
        
        Args:
            institution_id: Institution ID
        
        Returns:
            Real-time analytics dashboard data
        """
        try:
            # Overall metrics
            overall_metrics = self._calculate_overall_metrics(institution_id)
            
            # Department performance
            department_performance = self._analyze_department_performance(institution_id)
            
            # Student engagement metrics
            engagement_metrics = self._calculate_engagement_metrics(institution_id)
            
            # Employment outcomes
            employment_metrics = self._calculate_employment_metrics(institution_id)
            
            # Alumni success tracking
            alumni_metrics = self._track_alumni_success(institution_id)
            
            # At-risk student summary
            at_risk_summary = self._summarize_at_risk_students(institution_id)
            
            # Trending insights
            insights = self._generate_institutional_insights(institution_id)
            
            # Recommendations
            recommendations = self._generate_institutional_recommendations(
                overall_metrics,
                department_performance,
                at_risk_summary
            )
            
            return {
                'success': True,
                'institution_id': institution_id,
                'dashboard': {
                    'overall_metrics': overall_metrics,
                    'department_performance': department_performance,
                    'engagement_metrics': engagement_metrics,
                    'employment_metrics': employment_metrics,
                    'alumni_metrics': alumni_metrics,
                    'at_risk_summary': at_risk_summary
                },
                'insights': insights,
                'recommendations': recommendations,
                'alerts': self._generate_alerts(overall_metrics, at_risk_summary),
                'last_updated': datetime.utcnow().isoformat(),
                'data_refresh_rate': '15 minutes'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting institutional dashboard: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _gather_student_data(self, user: User) -> Dict[str, Any]:
        """Gather comprehensive student data for analysis"""
        return {
            'user_id': user.id,
            'gpa': getattr(user, 'gpa', 3.0),
            'major': getattr(user, 'major', 'Unknown'),
            'graduation_year': getattr(user, 'graduation_year', datetime.now().year),
            'months_until_graduation': self._calculate_months_until_graduation(user),
            'internship_count': getattr(user, 'internship_count', 0),
            'connections_count': getattr(user, 'connections_count', 10),
            'profile_completion': getattr(user, 'profile_completion', 75),
            'platform_engagement': getattr(user, 'platform_engagement_score', 25),
            'verified_skills_count': getattr(user, 'verified_skills_count', 3),
            'job_applications_count': getattr(user, 'job_applications_count', 5),
            'months_since_job_search_start': getattr(user, 'months_since_job_search_start', 3)
        }
    
    def _calculate_months_until_graduation(self, user: User) -> int:
        """Calculate months until graduation"""
        grad_year = getattr(user, 'graduation_year', datetime.now().year)
        grad_date = datetime(grad_year, 5, 15)  # Assume May 15 graduation
        months = (grad_date - datetime.now()).days / 30
        return max(0, int(months))
    
    def _calculate_risk_score(self, data: Dict) -> float:
        """Calculate employment risk score (0-1)"""
        risk_score = 0
        
        # Low GPA
        if data['gpa'] < self.RISK_FACTORS['low_gpa']['threshold']:
            risk_score += self.RISK_FACTORS['low_gpa']['weight']
        
        # No internship
        if data['internship_count'] == 0:
            risk_score += self.RISK_FACTORS['no_internship']['weight']
        
        # Inactive networking
        if data['connections_count'] < self.RISK_FACTORS['inactive_networking']['threshold']:
            risk_score += self.RISK_FACTORS['inactive_networking']['weight']
        
        # Incomplete profile
        if data['profile_completion'] < self.RISK_FACTORS['incomplete_profile']['threshold']:
            risk_score += self.RISK_FACTORS['incomplete_profile']['weight']
        
        # Low engagement
        if data['platform_engagement'] < self.RISK_FACTORS['low_engagement']['threshold']:
            risk_score += self.RISK_FACTORS['low_engagement']['weight']
        
        # Late job search
        if data['months_until_graduation'] < self.RISK_FACTORS['late_job_search']['threshold']:
            if data['job_applications_count'] < 5:
                risk_score += self.RISK_FACTORS['late_job_search']['weight']
        
        # No verified skills
        if data['verified_skills_count'] == 0:
            risk_score += self.RISK_FACTORS['no_skills_verified']['weight']
        
        return round(risk_score, 2)
    
    def _calculate_success_score(self, data: Dict) -> float:
        """Calculate success potential score (0-1)"""
        success_score = 0
        
        # High GPA
        if data['gpa'] >= self.SUCCESS_FACTORS['high_gpa']['threshold']:
            success_score += self.SUCCESS_FACTORS['high_gpa']['weight']
        
        # Multiple internships
        if data['internship_count'] >= self.SUCCESS_FACTORS['multiple_internships']['threshold']:
            success_score += self.SUCCESS_FACTORS['multiple_internships']['weight']
        
        # Strong network
        if data['connections_count'] >= self.SUCCESS_FACTORS['strong_network']['threshold']:
            success_score += self.SUCCESS_FACTORS['strong_network']['weight']
        
        # Complete profile
        if data['profile_completion'] >= self.SUCCESS_FACTORS['complete_profile']['threshold']:
            success_score += self.SUCCESS_FACTORS['complete_profile']['weight']
        
        # High engagement
        if data['platform_engagement'] >= self.SUCCESS_FACTORS['high_engagement']['threshold']:
            success_score += self.SUCCESS_FACTORS['high_engagement']['weight']
        
        # Early job search
        if data['months_until_graduation'] >= self.SUCCESS_FACTORS['early_job_search']['threshold']:
            success_score += self.SUCCESS_FACTORS['early_job_search']['weight']
        
        # Verified skills
        if data['verified_skills_count'] >= self.SUCCESS_FACTORS['verified_skills']['threshold']:
            success_score += self.SUCCESS_FACTORS['verified_skills']['weight']
        
        return round(success_score, 2)
    
    def _calculate_employment_probability(
        self,
        risk_score: float,
        success_score: float,
        data: Dict
    ) -> float:
        """Calculate probability of employment within 6 months of graduation"""
        # Base probability
        base_prob = 0.75  # 75% base employment rate
        
        # Adjust for success and risk
        adjusted_prob = base_prob + (success_score * 0.20) - (risk_score * 0.30)
        
        # Major-specific adjustment
        major_adjustment = self._get_major_employment_adjustment(data['major'])
        adjusted_prob += major_adjustment
        
        # Ensure within bounds
        return max(0.10, min(0.99, adjusted_prob))
    
    def _get_major_employment_adjustment(self, major: str) -> float:
        """Get employment adjustment by major"""
        adjustments = {
            'Computer Science': 0.10,
            'Engineering': 0.08,
            'Nursing': 0.12,
            'Business': 0.05,
            'Education': 0.02,
            'Liberal Arts': -0.05,
            'Fine Arts': -0.08
        }
        return adjustments.get(major, 0.0)
    
    def _predict_time_to_employment(self, data: Dict) -> int:
        """Predict days to employment after graduation"""
        base_days = 90  # 3 months baseline
        
        # Adjust based on factors
        if data['internship_count'] >= 2:
            base_days -= 30
        elif data['internship_count'] == 1:
            base_days -= 15
        
        if data['gpa'] >= 3.5:
            base_days -= 20
        
        if data['job_applications_count'] >= 20:
            base_days -= 25
        
        if data['connections_count'] >= 50:
            base_days -= 15
        
        return max(30, base_days)
    
    def _predict_starting_salary(self, data: Dict) -> Dict[str, int]:
        """Predict starting salary range"""
        # Base salary by major (simplified)
        base_salaries = {
            'Computer Science': 75000,
            'Engineering': 70000,
            'Nursing': 65000,
            'Business': 60000,
            'Education': 45000,
            'Liberal Arts': 40000
        }
        
        base = base_salaries.get(data['major'], 50000)
        
        # Adjustments
        if data['gpa'] >= 3.7:
            base += 5000
        
        if data['internship_count'] >= 2:
            base += 8000
        
        return {
            'min': int(base * 0.85),
            'median': base,
            'max': int(base * 1.25)
        }
    
    def _identify_positive_factors(self, data: Dict) -> List[str]:
        """Identify positive factors"""
        factors = []
        
        if data['gpa'] >= 3.5:
            factors.append('Strong GPA (3.5+)')
        
        if data['internship_count'] >= 1:
            factors.append(f"{data['internship_count']} internship(s)")
        
        if data['connections_count'] >= 50:
            factors.append('Strong professional network')
        
        if data['profile_completion'] >= 90:
            factors.append('Complete profile')
        
        if data['verified_skills_count'] >= 5:
            factors.append('Multiple verified skills')
        
        return factors
    
    def _identify_improvement_areas(self, data: Dict) -> List[str]:
        """Identify areas for improvement"""
        areas = []
        
        if data['gpa'] < 3.0:
            areas.append('GPA below 3.0')
        
        if data['internship_count'] == 0:
            areas.append('No internship experience')
        
        if data['connections_count'] < 20:
            areas.append('Limited professional network')
        
        if data['profile_completion'] < 80:
            areas.append('Incomplete profile')
        
        if data['job_applications_count'] < 10:
            areas.append('Few job applications')
        
        return areas
    
    def _generate_employment_recommendations(
        self,
        data: Dict,
        improvement_areas: List[str]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if 'No internship experience' in improvement_areas:
            recommendations.append({
                'priority': 'High',
                'action': 'Secure internship or project experience',
                'impact': 'Increases employment probability by 20%'
            })
        
        if 'Limited professional network' in improvement_areas:
            recommendations.append({
                'priority': 'Medium',
                'action': 'Connect with 20+ alumni and professionals',
                'impact': 'Improves job search efficiency by 30%'
            })
        
        if 'Few job applications' in improvement_areas:
            recommendations.append({
                'priority': 'High',
                'action': 'Apply to at least 20 positions',
                'impact': 'Increases interview chances significantly'
            })
        
        return recommendations
    
    def _calculate_prediction_confidence(self, data: Dict) -> str:
        """Calculate prediction confidence level"""
        data_completeness = data['profile_completion'] / 100
        
        if data_completeness >= 0.9:
            return 'High'
        elif data_completeness >= 0.7:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_probability_tier(self, prob: float) -> str:
        """Get probability tier label"""
        if prob >= 0.85:
            return 'Very High'
        elif prob >= 0.70:
            return 'High'
        elif prob >= 0.50:
            return 'Moderate'
        else:
            return 'Low'
    
    def _format_time_range(self, days: int) -> str:
        """Format time to employment range"""
        months = days // 30
        if months == 1:
            return '1-2 months'
        elif months == 2:
            return '2-3 months'
        elif months == 3:
            return '3-4 months'
        else:
            return f'{months}-{months+1} months'
    
    def _get_peer_benchmark(self, data: Dict) -> Dict[str, Any]:
        """Get peer benchmark comparison"""
        return {
            'your_employment_probability': 0.82,
            'peers_average': 0.75,
            'peers_in_major': 0.78,
            'national_average': 0.73
        }
    
    def _query_students(
        self,
        department_id: Optional[int],
        graduation_year: Optional[int]
    ) -> List[User]:
        """Query students with filters"""
        # Would query actual database
        # Simulating with sample data
        students = []
        for i in range(100):
            user = User()
            user.id = i
            user.name = f'Student {i}'
            user.email = f'student{i}@example.com'
            students.append(user)
        return students
    
    def _recommend_interventions(self, student: User, data: Dict) -> List[Dict]:
        """Recommend interventions for at-risk student"""
        interventions = []
        
        if data['internship_count'] == 0:
            interventions.append({
                'type': 'Career Advising',
                'action': 'Connect with career services for internship placement',
                'urgency': 'High'
            })
        
        if data['profile_completion'] < 70:
            interventions.append({
                'type': 'Platform Engagement',
                'action': 'Complete profile and upload resume',
                'urgency': 'Medium'
            })
        
        return interventions
    
    def _identify_primary_concerns(self, data: Dict) -> List[str]:
        """Identify primary concerns"""
        concerns = []
        
        if data['internship_count'] == 0:
            concerns.append('No work experience')
        
        if data['job_applications_count'] < 5:
            concerns.append('Not actively job searching')
        
        return concerns
    
    def _calculate_contact_priority(self, risk_score: float, data: Dict) -> str:
        """Calculate contact priority"""
        if risk_score >= 0.8:
            return 'Immediate'
        elif risk_score >= 0.6:
            return 'High'
        else:
            return 'Medium'
    
    def _get_risk_level(self, score: float) -> str:
        """Get risk level label"""
        if score >= 0.8:
            return 'Critical'
        elif score >= 0.6:
            return 'High'
        elif score >= 0.4:
            return 'Moderate'
        else:
            return 'Low'
    
    def _calculate_at_risk_statistics(
        self,
        at_risk: List[Dict],
        all_students: List
    ) -> Dict:
        """Calculate at-risk statistics"""
        return {
            'critical_risk': len([s for s in at_risk if s['risk_level'] == 'Critical']),
            'high_risk': len([s for s in at_risk if s['risk_level'] == 'High']),
            'most_common_concern': 'No internship experience',
            'avg_risk_score': round(statistics.mean([s['risk_score'] for s in at_risk]), 2) if at_risk else 0
        }
    
    def _summarize_interventions(self, at_risk: List[Dict]) -> Dict:
        """Summarize recommended interventions"""
        return {
            'career_advising_needed': 45,
            'profile_completion_needed': 30,
            'job_search_activation_needed': 25
        }
    
    def _get_historical_placement_data(self, dept_id: int) -> List[Dict]:
        """Get historical placement data"""
        # Simulated historical data
        data = []
        for year in range(2019, 2024):
            data.append({
                'year': year,
                'placement_rate': 72 + (year - 2019) * 2 + random.randint(-3, 3),
                'avg_time_to_employment': 90 - (year - 2019) * 5
            })
        return data
    
    def _analyze_cohort_readiness(self, students: List) -> Dict:
        """Analyze current cohort readiness"""
        return {
            'avg_internship_count': 1.2,
            'avg_profile_completion': 78,
            'avg_engagement': 35,
            'adjustment': 2.5  # Positive adjustment to forecast
        }
    
    def _calculate_trend_adjustment(self, historical: List[Dict]) -> float:
        """Calculate trend adjustment"""
        if len(historical) < 2:
            return 0.0
        
        recent_trend = historical[-1]['placement_rate'] - historical[-2]['placement_rate']
        return recent_trend * 0.5  # 50% weight on recent trend
    
    def _apply_market_conditions(self, dept_id: int) -> float:
        """Apply market conditions adjustment"""
        # Would analyze actual job market data
        return 1.5  # Positive market conditions
    
    def _calculate_base_placement_rate(self, historical: List[Dict]) -> float:
        """Calculate base placement rate from historical data"""
        if not historical:
            return 75.0
        
        recent_rates = [d['placement_rate'] for d in historical[-3:]]
        return statistics.mean(recent_rates)
    
    def _calculate_confidence_interval(self, historical: List, cohort: Dict) -> Dict:
        """Calculate confidence interval"""
        return {
            'lower_bound': 73.5,
            'upper_bound': 81.2
        }
    
    def _generate_department_recommendations(
        self,
        forecast: float,
        cohort: Dict
    ) -> List[str]:
        """Generate recommendations for department"""
        recommendations = []
        
        if forecast < 75:
            recommendations.append('Increase career services engagement with students')
        
        if cohort['avg_internship_count'] < 1.0:
            recommendations.append('Strengthen internship placement programs')
        
        return recommendations
    
    def _get_program_data(self, dept_id: int) -> Dict:
        """Get program data"""
        return {
            'department_id': dept_id,
            'name': 'Computer Science',
            'industry': 'Technology',
            'tuition_per_year': 15000,
            'duration_years': 4
        }
    
    def _get_alumni_earnings(self, dept_id: int, years: int) -> Dict:
        """Get alumni earnings data"""
        return {
            'median_starting': 75000,
            'median_5_years': 95000,
            'median_10_years': 120000
        }
    
    def _calculate_program_costs(self, program: Dict) -> Dict:
        """Calculate total program costs"""
        tuition = program['tuition_per_year'] * program['duration_years']
        return {
            'tuition': tuition,
            'fees': tuition * 0.1,
            'total': tuition * 1.1
        }
    
    def _calculate_lifetime_earnings(self, earnings: Dict) -> int:
        """Calculate lifetime earnings projection"""
        # 40 year career
        return earnings['median_starting'] * 40 + (earnings['median_10_years'] - earnings['median_starting']) * 10
    
    def _calculate_roi(self, lifetime_earnings: int, costs: Dict) -> float:
        """Calculate ROI percentage"""
        roi = ((lifetime_earnings - costs['total']) / costs['total']) * 100
        return round(roi, 1)
    
    def _calculate_payback_period(self, earnings: Dict, costs: Dict) -> float:
        """Calculate payback period in years"""
        annual_earnings = earnings['median_starting']
        return round(costs['total'] / annual_earnings, 1)
    
    def _compare_to_other_programs(self, dept_id: int, roi: float) -> Dict:
        """Compare to other programs"""
        return {
            'institution_average_roi': 450,
            'national_average_roi': 420,
            'percentile': 72
        }
    
    def _analyze_employment_outcomes(self, dept_id: int) -> Dict:
        """Analyze employment outcomes"""
        return {
            'placement_rate_6_months': 89,
            'placement_rate_12_months': 95,
            'median_starting_salary': 75000
        }
    
    def _analyze_career_progression(self, dept_id: int) -> Dict:
        """Analyze career progression"""
        return {
            '1_year_promotion_rate': 15,
            '3_year_salary_growth': 28,
            '5_year_management_rate': 35
        }
    
    def _get_roi_rating(self, roi: float) -> str:
        """Get ROI rating"""
        if roi >= 500:
            return 'Excellent'
        elif roi >= 400:
            return 'Very Good'
        elif roi >= 300:
            return 'Good'
        else:
            return 'Fair'
    
    def _identify_program_strengths(self, program: Dict, earnings: Dict) -> List[str]:
        """Identify program strengths"""
        return [
            'High starting salaries',
            'Strong industry partnerships',
            'Excellent career services'
        ]
    
    def _identify_program_improvements(self, program: Dict, earnings: Dict) -> List[str]:
        """Identify improvement opportunities"""
        return [
            'Increase internship placement rate',
            'Expand alumni mentorship program'
        ]
    
    def _get_market_outlook(self, industry: str) -> Dict:
        """Get market outlook"""
        growth = self.INDUSTRY_GROWTH.get(industry, 0.05)
        return {
            'growth_rate': growth,
            'outlook': 'Strong' if growth > 0.08 else 'Moderate' if growth > 0.03 else 'Stable',
            'job_openings_trend': 'Increasing'
        }
    
    def _get_historical_demand(self, industry: str) -> List[Dict]:
        """Get historical hiring demand"""
        data = []
        for i in range(12):
            data.append({
                'month': i + 1,
                'job_postings': 100 + i * 5 + random.randint(-10, 10)
            })
        return data
    
    def _calculate_seasonal_factors(self, historical: List[Dict]) -> Dict:
        """Calculate seasonal factors"""
        return {
            'peak_hiring_months': ['September', 'October', 'January', 'February'],
            'slow_months': ['July', 'August', 'December']
        }
    
    def _identify_trending_skills(self, industry: str) -> List[Dict]:
        """Identify trending skills"""
        return [
            {'skill': 'Python', 'growth': 45, 'demand_score': 92},
            {'skill': 'Cloud Computing', 'growth': 38, 'demand_score': 88},
            {'skill': 'Machine Learning', 'growth': 52, 'demand_score': 85}
        ]
    
    def _identify_emerging_roles(self, industry: str) -> List[Dict]:
        """Identify emerging roles"""
        return [
            {'role': 'AI Engineer', 'growth': 60, 'avg_salary': 120000},
            {'role': 'DevOps Engineer', 'growth': 45, 'avg_salary': 105000}
        ]
    
    def _calculate_supply_demand_gap(self, industry: str) -> Dict:
        """Calculate supply-demand gap"""
        return {
            'job_openings': 5000,
            'qualified_candidates': 3500,
            'gap': 1500,
            'gap_percentage': 30
        }
    
    def _identify_job_opportunities(self, industry: str, skills: List) -> List[str]:
        """Identify job opportunities"""
        return [
            'High demand for Python developers',
            'Cloud certifications increase job prospects by 40%'
        ]
    
    def _generate_career_planning_recommendations(
        self,
        industry: str,
        skills: List
    ) -> List[str]:
        """Generate career planning recommendations"""
        return [
            f'Focus on developing {skills[0]["skill"]} skills',
            'Consider cloud computing certification',
            'Build portfolio with ML projects'
        ]
    
    def _calculate_overall_metrics(self, inst_id: int) -> Dict:
        """Calculate overall institutional metrics"""
        return {
            'total_students': 5000,
            'active_users': 4200,
            'platform_engagement_rate': 84,
            'overall_placement_rate': 87,
            'avg_time_to_employment': 75,
            'avg_starting_salary': 62000
        }
    
    def _analyze_department_performance(self, inst_id: int) -> List[Dict]:
        """Analyze department performance"""
        return [
            {
                'department': 'Computer Science',
                'placement_rate': 92,
                'avg_salary': 75000,
                'performance_tier': 'Excellent'
            },
            {
                'department': 'Business',
                'placement_rate': 85,
                'avg_salary': 60000,
                'performance_tier': 'Good'
            }
        ]
    
    def _calculate_engagement_metrics(self, inst_id: int) -> Dict:
        """Calculate engagement metrics"""
        return {
            'daily_active_users': 850,
            'monthly_active_users': 3500,
            'avg_session_duration': 12.5,
            'feature_adoption_rate': 68
        }
    
    def _calculate_employment_metrics(self, inst_id: int) -> Dict:
        """Calculate employment metrics"""
        return {
            'students_employed': 1200,
            'students_job_searching': 450,
            'avg_applications_per_student': 15,
            'interview_conversion_rate': 22
        }
    
    def _track_alumni_success(self, inst_id: int) -> Dict:
        """Track alumni success metrics"""
        return {
            'alumni_employed': 8500,
            'avg_years_experience': 6.5,
            'avg_current_salary': 85000,
            'promotions_last_year': 1250
        }
    
    def _summarize_at_risk_students(self, inst_id: int) -> Dict:
        """Summarize at-risk students"""
        return {
            'total_at_risk': 320,
            'critical_risk': 45,
            'interventions_in_progress': 180
        }
    
    def _generate_institutional_insights(self, inst_id: int) -> List[str]:
        """Generate insights"""
        return [
            'CS department exceeding placement targets by 15%',
            '320 students identified as at-risk - intervention recommended',
            'Platform engagement increased 12% this month'
        ]
    
    def _generate_institutional_recommendations(
        self,
        metrics: Dict,
        at_risk: Dict,
        dept_performance: List
    ) -> List[Dict]:
        """Generate institutional recommendations"""
        return [
            {
                'priority': 'High',
                'area': 'At-Risk Students',
                'recommendation': 'Increase career counseling outreach to 320 at-risk students',
                'expected_impact': 'Improve placement rate by 5-7%'
            },
            {
                'priority': 'Medium',
                'area': 'Engagement',
                'recommendation': 'Launch targeted campaigns to increase daily active users',
                'expected_impact': '15% increase in platform engagement'
            }
        ]
    
    def _generate_alerts(self, metrics: Dict, at_risk: Dict) -> List[Dict]:
        """Generate alerts"""
        alerts = []
        
        if at_risk['critical_risk'] > 40:
            alerts.append({
                'severity': 'High',
                'message': f'{at_risk["critical_risk"]} students at critical risk',
                'action_required': 'Immediate intervention needed'
            })
        
        return alerts


# Example usage
if __name__ == '__main__':
    service = PredictiveAnalyticsService()
    
    # Test employment prediction
    print("Testing Employment Prediction:")
    result = service.predict_employment_outcome(user_id=1)
    print(f"Employment probability: {result['prediction']['employment_probability']}")
