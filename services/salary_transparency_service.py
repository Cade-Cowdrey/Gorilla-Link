"""
Salary Transparency Service
Crowdsourced salary database with anonymous sharing and offer comparison

Features:
- Anonymous salary submissions
- Salary insights by role, location, experience
- Offer comparison tool
- Total compensation calculator
- Negotiation leverage data
- Historical salary trends
- Cost of living adjustments
- Industry benchmarking
- Demographic analysis (optional, anonymous)
- Employer salary ratings

Revenue Model:
- Free basic access for students
- Employer premium access: $2,000-5,000/year
- Data licensing: $10,000+/year
- Premium analytics: $30/month for advanced insights
Target: $150,000+ annually
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import statistics
from collections import defaultdict
import hashlib

from models import db, User, Company, Job
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


class SalaryTransparencyService:
    """Service for salary transparency and compensation insights"""
    
    # Compensation components
    COMP_COMPONENTS = [
        'base_salary',
        'signing_bonus',
        'annual_bonus',
        'stock_options',
        'equity_value',
        'benefits_value',
        'retirement_match',
        'other_comp'
    ]
    
    # Experience levels
    EXPERIENCE_LEVELS = {
        'entry': {'min_years': 0, 'max_years': 2, 'label': 'Entry Level'},
        'mid': {'min_years': 3, 'max_years': 5, 'label': 'Mid-Level'},
        'senior': {'min_years': 6, 'max_years': 10, 'label': 'Senior'},
        'lead': {'min_years': 11, 'max_years': 15, 'label': 'Lead/Principal'},
        'executive': {'min_years': 16, 'max_years': 99, 'label': 'Executive'}
    }
    
    # Cost of living multipliers by city (relative to national average)
    COL_MULTIPLIERS = {
        'San Francisco': 1.62,
        'New York': 1.49,
        'Seattle': 1.37,
        'Boston': 1.31,
        'Los Angeles': 1.27,
        'Washington DC': 1.25,
        'San Diego': 1.21,
        'Chicago': 1.08,
        'Austin': 1.04,
        'Denver': 1.03,
        'Atlanta': 0.97,
        'Phoenix': 0.95,
        'Dallas': 0.93,
        'Houston': 0.91,
        'National Average': 1.00
    }

    def __init__(self):
        """Initialize salary transparency service"""
        self.logger = logger
    
    def submit_salary_data(
        self,
        user_id: int,
        salary_data: Dict[str, Any],
        anonymous: bool = True
    ) -> Dict[str, Any]:
        """
        Submit salary data anonymously or attributed
        
        Args:
            user_id: User submitting data
            salary_data: Compensation details
            anonymous: Whether to keep submission anonymous
        
        Returns:
            Submission confirmation and contribution stats
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Validate required fields
            required = ['job_title', 'base_salary', 'location', 'years_experience']
            missing = [f for f in required if f not in salary_data]
            if missing:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing)}'
                }
            
            # Create salary record
            salary_record = {
                'user_id': None if anonymous else user_id,
                'job_title': salary_data['job_title'],
                'company_id': salary_data.get('company_id'),
                'company_name': salary_data.get('company_name'),
                'location': salary_data['location'],
                'base_salary': salary_data['base_salary'],
                'signing_bonus': salary_data.get('signing_bonus', 0),
                'annual_bonus': salary_data.get('annual_bonus', 0),
                'stock_options': salary_data.get('stock_options', 0),
                'equity_value': salary_data.get('equity_value', 0),
                'benefits_value': salary_data.get('benefits_value', 0),
                'total_comp': self._calculate_total_comp(salary_data),
                'years_experience': salary_data['years_experience'],
                'education_level': salary_data.get('education_level'),
                'industry': salary_data.get('industry'),
                'employment_type': salary_data.get('employment_type', 'full_time'),
                'remote': salary_data.get('remote', False),
                'submitted_at': datetime.utcnow(),
                'verified': self._verify_submission(user, salary_data),
                'anonymous': anonymous,
                'data_hash': self._generate_data_hash(salary_data)
            }
            
            # Save to database (would use SalaryData model)
            salary_id = self._save_salary_record(salary_record)
            
            # Update user contribution count
            contribution_count = self._increment_user_contributions(user_id)
            
            # Calculate percentile
            percentile = self._calculate_percentile(
                salary_record['base_salary'],
                salary_record['job_title'],
                salary_record['years_experience']
            )
            
            return {
                'success': True,
                'salary_id': salary_id,
                'anonymous': anonymous,
                'your_contributions': contribution_count,
                'salary_percentile': percentile,
                'total_comp': salary_record['total_comp'],
                'unlocked_insights': self._get_unlocked_insights(contribution_count),
                'message': 'Thank you for contributing to salary transparency!'
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting salary data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_salary_insights(
        self,
        job_title: str,
        location: str = None,
        years_experience: int = None,
        education_level: str = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive salary insights for a role
        
        Args:
            job_title: Job title to search
            location: Location filter (optional)
            years_experience: Years of experience (optional)
            education_level: Education level filter (optional)
        
        Returns:
            Detailed salary statistics and insights
        """
        try:
            # Get matching salary records
            records = self._query_salary_data(
                job_title=job_title,
                location=location,
                years_experience=years_experience,
                education_level=education_level
            )
            
            if not records:
                return {
                    'success': True,
                    'data_available': False,
                    'message': f'Insufficient data for {job_title}. Be the first to contribute!',
                    'similar_roles': self._find_similar_roles(job_title)
                }
            
            # Calculate statistics
            base_salaries = [r['base_salary'] for r in records]
            total_comps = [r['total_comp'] for r in records]
            
            stats = {
                'count': len(records),
                'base_salary': {
                    'min': min(base_salaries),
                    'max': max(base_salaries),
                    'median': statistics.median(base_salaries),
                    'mean': statistics.mean(base_salaries),
                    'p25': self._percentile(base_salaries, 25),
                    'p75': self._percentile(base_salaries, 75),
                    'p90': self._percentile(base_salaries, 90)
                },
                'total_compensation': {
                    'min': min(total_comps),
                    'max': max(total_comps),
                    'median': statistics.median(total_comps),
                    'mean': statistics.mean(total_comps),
                    'p25': self._percentile(total_comps, 25),
                    'p75': self._percentile(total_comps, 75)
                }
            }
            
            # Breakdown by experience level
            by_experience = self._group_by_experience(records)
            
            # Breakdown by location
            by_location = self._group_by_location(records)
            
            # Company comparisons
            top_paying_companies = self._get_top_paying_companies(records)
            
            # Compensation components analysis
            comp_breakdown = self._analyze_comp_components(records)
            
            # Trends over time
            trends = self._calculate_salary_trends(job_title)
            
            return {
                'success': True,
                'data_available': True,
                'job_title': job_title,
                'location': location or 'All Locations',
                'statistics': stats,
                'by_experience_level': by_experience,
                'by_location': by_location,
                'top_paying_companies': top_paying_companies,
                'compensation_breakdown': comp_breakdown,
                'trends': trends,
                'last_updated': datetime.utcnow().isoformat(),
                'data_sources': len(records)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary insights: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def compare_offers(
        self,
        user_id: int,
        offers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple job offers side-by-side
        
        Args:
            user_id: User comparing offers
            offers: List of offer details
        
        Returns:
            Detailed comparison analysis
        """
        try:
            if len(offers) < 2:
                return {'success': False, 'error': 'Need at least 2 offers to compare'}
            
            comparisons = []
            
            for idx, offer in enumerate(offers):
                # Calculate total compensation
                total_comp = self._calculate_total_comp(offer)
                
                # Adjust for cost of living
                col_adjusted = self._adjust_for_col(
                    total_comp,
                    offer.get('location', 'National Average')
                )
                
                # Get market comparison
                market_data = self.get_salary_insights(
                    job_title=offer['job_title'],
                    location=offer.get('location'),
                    years_experience=offer.get('years_experience')
                )
                
                # Calculate offer strength
                strength = self._calculate_offer_strength(offer, market_data)
                
                comparisons.append({
                    'offer_id': idx + 1,
                    'company': offer.get('company_name', f'Company {idx + 1}'),
                    'job_title': offer['job_title'],
                    'location': offer.get('location'),
                    'base_salary': offer.get('base_salary', 0),
                    'total_comp': total_comp,
                    'col_adjusted_comp': col_adjusted,
                    'market_percentile': strength['percentile'],
                    'vs_market_median': strength['vs_median'],
                    'offer_strength': strength['rating'],
                    'breakdown': self._get_comp_breakdown(offer),
                    'benefits': offer.get('benefits', {}),
                    'non_financial': {
                        'remote_work': offer.get('remote', False),
                        'pto_days': offer.get('pto_days'),
                        'growth_opportunities': offer.get('growth_opportunities'),
                        'company_culture': offer.get('company_culture_rating')
                    }
                })
            
            # Rank offers
            ranked = self._rank_offers(comparisons)
            
            # Generate recommendations
            recommendations = self._generate_offer_recommendations(ranked)
            
            return {
                'success': True,
                'offers_compared': len(offers),
                'comparisons': ranked,
                'best_overall': ranked[0]['offer_id'],
                'best_total_comp': max(comparisons, key=lambda x: x['total_comp'])['offer_id'],
                'best_col_adjusted': max(comparisons, key=lambda x: x['col_adjusted_comp'])['offer_id'],
                'recommendations': recommendations,
                'decision_framework': self._get_decision_framework()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing offers: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_negotiation_leverage(
        self,
        job_title: str,
        current_offer: Dict[str, Any],
        user_qualifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate negotiation leverage and provide data-backed arguments
        
        Args:
            job_title: Position title
            current_offer: Current offer details
            user_qualifications: User's qualifications
        
        Returns:
            Negotiation leverage analysis
        """
        try:
            # Get market data
            market_data = self.get_salary_insights(
                job_title=job_title,
                years_experience=user_qualifications.get('years_experience')
            )
            
            if not market_data.get('data_available'):
                return {
                    'success': False,
                    'error': 'Insufficient market data for negotiation analysis'
                }
            
            current_base = current_offer.get('base_salary', 0)
            market_median = market_data['statistics']['base_salary']['median']
            market_p75 = market_data['statistics']['base_salary']['p75']
            
            # Calculate gaps
            gap_from_median = market_median - current_base
            gap_from_p75 = market_p75 - current_base
            
            # Assess leverage factors
            leverage_factors = []
            leverage_score = 0
            
            # Factor 1: Below market median
            if current_base < market_median:
                leverage_factors.append({
                    'factor': 'Below Market Median',
                    'impact': 'High',
                    'data': f'Current offer is ${gap_from_median:,.0f} below market median',
                    'script': f'Based on market data, the median salary for this role is ${market_median:,.0f}'
                })
                leverage_score += 30
            
            # Factor 2: Strong qualifications
            if user_qualifications.get('education_level') == 'Masters' or user_qualifications.get('education_level') == 'PhD':
                leverage_factors.append({
                    'factor': 'Advanced Degree',
                    'impact': 'Medium',
                    'data': 'Advanced degree holders earn 15-25% more on average',
                    'script': 'My advanced degree brings additional value to this role'
                })
                leverage_score += 20
            
            # Factor 3: Multiple offers
            if user_qualifications.get('has_competing_offers'):
                leverage_factors.append({
                    'factor': 'Competing Offers',
                    'impact': 'High',
                    'data': 'Candidates with multiple offers have 40% more negotiating power',
                    'script': 'I have other offers to consider, but this is my top choice'
                })
                leverage_score += 35
            
            # Factor 4: Specialized skills
            if user_qualifications.get('specialized_skills'):
                leverage_factors.append({
                    'factor': 'In-Demand Skills',
                    'impact': 'Medium',
                    'data': 'Specialized skills command premium compensation',
                    'script': 'My expertise in [specific skill] is directly relevant to this role'
                })
                leverage_score += 15
            
            # Calculate recommended counteroffer
            counteroffer = self._calculate_counteroffer(
                current_offer,
                market_data,
                leverage_score
            )
            
            return {
                'success': True,
                'leverage_score': min(leverage_score, 100),
                'leverage_rating': self._get_leverage_rating(leverage_score),
                'leverage_factors': leverage_factors,
                'market_position': {
                    'current_offer': current_base,
                    'market_median': market_median,
                    'market_p75': market_p75,
                    'percentile': self._calculate_percentile(current_base, job_title, user_qualifications.get('years_experience'))
                },
                'recommended_counteroffer': counteroffer,
                'negotiation_scripts': self._generate_negotiation_scripts(leverage_factors, counteroffer),
                'tactics': self._get_negotiation_tactics(leverage_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating negotiation leverage: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_salary_trends(
        self,
        job_title: str,
        time_period: str = '5_years'
    ) -> Dict[str, Any]:
        """
        Get historical salary trends and projections
        
        Args:
            job_title: Job title
            time_period: Time period (1_year, 3_years, 5_years, 10_years)
        
        Returns:
            Salary trend analysis
        """
        try:
            # Get historical data
            historical_data = self._get_historical_salary_data(job_title, time_period)
            
            if not historical_data:
                return {
                    'success': True,
                    'data_available': False,
                    'message': 'Insufficient historical data'
                }
            
            # Calculate year-over-year growth
            yoy_growth = self._calculate_yoy_growth(historical_data)
            
            # Project future salaries
            projections = self._project_future_salaries(historical_data)
            
            # Industry trends
            industry_trends = self._get_industry_trends(job_title)
            
            return {
                'success': True,
                'data_available': True,
                'job_title': job_title,
                'time_period': time_period,
                'historical_data': historical_data,
                'yoy_growth': yoy_growth,
                'avg_annual_growth': statistics.mean(yoy_growth.values()) if yoy_growth else 0,
                'projections': projections,
                'industry_trends': industry_trends,
                'factors_affecting_growth': self._get_growth_factors(job_title)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary trends: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_cost_of_living_adjustment(
        self,
        salary: int,
        from_location: str,
        to_location: str
    ) -> Dict[str, Any]:
        """
        Calculate cost of living adjusted salary
        
        Args:
            salary: Current salary
            from_location: Current location
            to_location: Target location
        
        Returns:
            Adjusted salary calculations
        """
        try:
            from_col = self.COL_MULTIPLIERS.get(from_location, 1.0)
            to_col = self.COL_MULTIPLIERS.get(to_location, 1.0)
            
            adjustment_factor = to_col / from_col
            adjusted_salary = int(salary * adjustment_factor)
            difference = adjusted_salary - salary
            
            return {
                'success': True,
                'current_salary': salary,
                'current_location': from_location,
                'target_location': to_location,
                'adjusted_salary': adjusted_salary,
                'difference': difference,
                'adjustment_percentage': round((adjustment_factor - 1) * 100, 1),
                'from_col_index': from_col,
                'to_col_index': to_col,
                'explanation': self._get_col_explanation(from_location, to_location, adjustment_factor)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating COL adjustment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _calculate_total_comp(self, salary_data: Dict[str, Any]) -> int:
        """Calculate total compensation"""
        total = 0
        for component in self.COMP_COMPONENTS:
            total += salary_data.get(component, 0)
        return total
    
    def _verify_submission(self, user: User, salary_data: Dict) -> bool:
        """Verify salary submission authenticity"""
        # Check if user has verified email from company domain
        if user.email and salary_data.get('company_name'):
            company_domain = salary_data.get('company_domain')
            if company_domain and company_domain in user.email:
                return True
        return False
    
    def _generate_data_hash(self, data: Dict) -> str:
        """Generate hash to prevent duplicate submissions"""
        key_fields = f"{data['job_title']}{data['base_salary']}{data['location']}"
        return hashlib.md5(key_fields.encode()).hexdigest()
    
    def _save_salary_record(self, record: Dict) -> str:
        """Save salary record to database"""
        # Would save to SalaryData model
        salary_id = hashlib.md5(str(record).encode()).hexdigest()[:12]
        self.logger.info(f"Saved salary record: {salary_id}")
        return salary_id
    
    def _increment_user_contributions(self, user_id: int) -> int:
        """Increment user's contribution count"""
        try:
            from models import User
            
            user = User.query.get(user_id)
            if user:
                # Assuming you have a contributions field on User model
                if not hasattr(user, 'salary_contributions'):
                    # If field doesn't exist, would need migration
                    # For now, return count from SalaryData
                    from models_extended import SalaryData
                    count = SalaryData.query.filter_by(submitted_by=user_id).count()
                    return count
                else:
                    user.salary_contributions = (user.salary_contributions or 0) + 1
                    db.session.commit()
                    return user.salary_contributions
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error incrementing contributions: {e}")
            return 1
    
    def _calculate_percentile(self, salary: int, job_title: str, years_exp: int) -> int:
        """Calculate salary percentile"""
        # Simplified calculation
        if salary > 150000:
            return 90
        elif salary > 120000:
            return 75
        elif salary > 90000:
            return 60
        elif salary > 70000:
            return 50
        else:
            return 25
    
    def _get_unlocked_insights(self, contribution_count: int) -> List[str]:
        """Get insights unlocked by contributing"""
        insights = ['Basic salary statistics']
        if contribution_count >= 1:
            insights.append('Company comparisons')
        if contribution_count >= 3:
            insights.append('Detailed compensation breakdowns')
        if contribution_count >= 5:
            insights.append('Historical trends and projections')
        return insights
    
    def _query_salary_data(
        self,
        job_title: str,
        location: str = None,
        years_experience: int = None,
        education_level: str = None
    ) -> List[Dict]:
        """Query salary database"""
        # Would query SalaryData model with filters
        # Simulated data for demonstration
        sample_data = []
        for i in range(50):
            sample_data.append({
                'base_salary': 70000 + (i * 2000),
                'total_comp': 80000 + (i * 2500),
                'location': location or 'San Francisco',
                'years_experience': years_experience or (i % 10),
                'company_name': f'Company {i % 10}'
            })
        return sample_data
    
    def _find_similar_roles(self, job_title: str) -> List[str]:
        """Find similar job titles"""
        return [
            'Software Engineer',
            'Senior Software Engineer',
            'Frontend Developer',
            'Backend Developer'
        ]
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _group_by_experience(self, records: List[Dict]) -> Dict[str, Dict]:
        """Group salary data by experience level"""
        grouped = defaultdict(list)
        for record in records:
            years = record['years_experience']
            for level, config in self.EXPERIENCE_LEVELS.items():
                if config['min_years'] <= years <= config['max_years']:
                    grouped[level].append(record['base_salary'])
                    break
        
        result = {}
        for level, salaries in grouped.items():
            if salaries:
                result[self.EXPERIENCE_LEVELS[level]['label']] = {
                    'count': len(salaries),
                    'median': statistics.median(salaries),
                    'min': min(salaries),
                    'max': max(salaries)
                }
        
        return result
    
    def _group_by_location(self, records: List[Dict]) -> Dict[str, Dict]:
        """Group salary data by location"""
        grouped = defaultdict(list)
        for record in records:
            grouped[record['location']].append(record['base_salary'])
        
        result = {}
        for location, salaries in grouped.items():
            if salaries:
                result[location] = {
                    'count': len(salaries),
                    'median': statistics.median(salaries),
                    'col_adjusted': int(statistics.median(salaries) / self.COL_MULTIPLIERS.get(location, 1.0))
                }
        
        return result
    
    def _get_top_paying_companies(self, records: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top paying companies"""
        company_salaries = defaultdict(list)
        for record in records:
            if record.get('company_name'):
                company_salaries[record['company_name']].append(record['total_comp'])
        
        top_companies = []
        for company, salaries in company_salaries.items():
            if len(salaries) >= 3:  # Minimum data points
                top_companies.append({
                    'company': company,
                    'median_comp': statistics.median(salaries),
                    'data_points': len(salaries)
                })
        
        return sorted(top_companies, key=lambda x: x['median_comp'], reverse=True)[:limit]
    
    def _analyze_comp_components(self, records: List[Dict]) -> Dict[str, Any]:
        """Analyze compensation component breakdown"""
        components = defaultdict(list)
        for record in records:
            for comp in self.COMP_COMPONENTS:
                if record.get(comp):
                    components[comp].append(record[comp])
        
        analysis = {}
        for comp, values in components.items():
            if values:
                analysis[comp] = {
                    'median': statistics.median(values),
                    'avg_percentage': round((statistics.mean(values) / statistics.mean([r['total_comp'] for r in records])) * 100, 1)
                }
        
        return analysis
    
    def _calculate_salary_trends(self, job_title: str) -> Dict[str, Any]:
        """Calculate salary trends over time"""
        return {
            '2023': 85000,
            '2024': 92000,
            '2025': 98000,
            'growth_rate': '7.5% annually'
        }
    
    def _adjust_for_col(self, salary: int, location: str) -> int:
        """Adjust salary for cost of living"""
        col_index = self.COL_MULTIPLIERS.get(location, 1.0)
        return int(salary / col_index)
    
    def _calculate_offer_strength(self, offer: Dict, market_data: Dict) -> Dict[str, Any]:
        """Calculate strength of job offer"""
        if not market_data.get('data_available'):
            return {'percentile': 50, 'vs_median': 0, 'rating': 'Unknown'}
        
        offer_salary = offer.get('base_salary', 0)
        market_median = market_data['statistics']['base_salary']['median']
        
        percentile = self._calculate_percentile(offer_salary, offer['job_title'], offer.get('years_experience', 0))
        vs_median = offer_salary - market_median
        
        if percentile >= 75:
            rating = 'Excellent'
        elif percentile >= 60:
            rating = 'Good'
        elif percentile >= 40:
            rating = 'Fair'
        else:
            rating = 'Below Average'
        
        return {
            'percentile': percentile,
            'vs_median': vs_median,
            'vs_median_percentage': round((vs_median / market_median) * 100, 1),
            'rating': rating
        }
    
    def _get_comp_breakdown(self, offer: Dict) -> Dict[str, int]:
        """Get compensation breakdown"""
        return {
            'base_salary': offer.get('base_salary', 0),
            'signing_bonus': offer.get('signing_bonus', 0),
            'annual_bonus': offer.get('annual_bonus', 0),
            'equity': offer.get('equity_value', 0),
            'benefits': offer.get('benefits_value', 0)
        }
    
    def _rank_offers(self, comparisons: List[Dict]) -> List[Dict]:
        """Rank offers by overall attractiveness"""
        # Score based on multiple factors
        for offer in comparisons:
            score = 0
            score += offer['total_comp'] / 1000  # Compensation weight
            score += offer['market_percentile'] * 0.5  # Market position weight
            score += (offer['non_financial'].get('pto_days', 0) or 15) * 2  # PTO weight
            offer['overall_score'] = score
        
        return sorted(comparisons, key=lambda x: x['overall_score'], reverse=True)
    
    def _generate_offer_recommendations(self, ranked_offers: List[Dict]) -> List[str]:
        """Generate offer recommendations"""
        recommendations = []
        best = ranked_offers[0]
        
        recommendations.append(f"Best overall offer: {best['company']} with ${best['total_comp']:,.0f} total compensation")
        
        if best['market_percentile'] < 50:
            recommendations.append("Consider negotiating - offer is below market median")
        
        if best['non_financial']['remote_work']:
            recommendations.append("Remote work adds significant value (equivalent to 10-15% salary increase)")
        
        return recommendations
    
    def _get_decision_framework(self) -> Dict[str, int]:
        """Get decision-making framework weights"""
        return {
            'total_compensation': 40,
            'growth_opportunities': 20,
            'work_life_balance': 15,
            'company_culture': 15,
            'location': 10
        }
    
    def _calculate_counteroffer(
        self,
        current_offer: Dict,
        market_data: Dict,
        leverage_score: int
    ) -> Dict[str, Any]:
        """Calculate recommended counteroffer"""
        current_base = current_offer.get('base_salary', 0)
        market_median = market_data['statistics']['base_salary']['median']
        market_p75 = market_data['statistics']['base_salary']['p75']
        
        # Calculate target based on leverage
        if leverage_score >= 70:
            target = market_p75
        elif leverage_score >= 50:
            target = int((market_median + market_p75) / 2)
        else:
            target = market_median
        
        return {
            'current_offer': current_base,
            'recommended_counter': target,
            'increase_amount': target - current_base,
            'increase_percentage': round(((target - current_base) / current_base) * 100, 1),
            'confidence_level': 'High' if leverage_score >= 70 else 'Medium' if leverage_score >= 50 else 'Low'
        }
    
    def _get_leverage_rating(self, score: int) -> str:
        """Get leverage rating from score"""
        if score >= 80:
            return 'Very Strong'
        elif score >= 60:
            return 'Strong'
        elif score >= 40:
            return 'Moderate'
        else:
            return 'Limited'
    
    def _generate_negotiation_scripts(self, factors: List[Dict], counteroffer: Dict) -> Dict[str, str]:
        """Generate negotiation scripts"""
        return {
            'opening': f"Thank you for the offer. I'm very excited about the opportunity. Based on my research and the value I'll bring, I was hoping we could discuss a salary of ${counteroffer['recommended_counter']:,.0f}.",
            'data_backed': f"Based on market data for this role, the median compensation is ${counteroffer['current_offer']:,.0f}, and I believe my {factors[0]['factor'] if factors else 'qualifications'} justify positioning at that level.",
            'alternative': "If salary flexibility is limited, I'd be interested in discussing other aspects of the compensation package, such as signing bonus, equity, or additional vacation days."
        }
    
    def _get_negotiation_tactics(self, leverage_score: int) -> List[str]:
        """Get negotiation tactics based on leverage"""
        tactics = [
            "Always negotiate - 85% of employers expect it",
            "Be specific with numbers backed by data",
            "Focus on value you'll bring, not what you need",
            "Never accept or reject on the spot - take 24-48 hours"
        ]
        
        if leverage_score >= 60:
            tactics.append("You have strong leverage - aim high with confidence")
        else:
            tactics.append("Build rapport first, then discuss compensation")
        
        return tactics
    
    def _get_historical_salary_data(self, job_title: str, period: str) -> Dict[int, int]:
        """Get historical salary data"""
        # Simulated data
        current_year = datetime.now().year
        data = {}
        for i in range(5):
            year = current_year - i
            data[year] = 85000 + (i * 5000)  # Increasing trend
        return data
    
    def _calculate_yoy_growth(self, historical_data: Dict) -> Dict[str, float]:
        """Calculate year-over-year growth"""
        years = sorted(historical_data.keys())
        growth = {}
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            growth[f"{prev_year}-{curr_year}"] = round(
                ((historical_data[curr_year] - historical_data[prev_year]) / historical_data[prev_year]) * 100,
                2
            )
        return growth
    
    def _project_future_salaries(self, historical_data: Dict) -> Dict[int, int]:
        """Project future salaries"""
        # Simple linear projection
        years = sorted(historical_data.keys())
        values = [historical_data[y] for y in years]
        avg_growth = statistics.mean([values[i] - values[i-1] for i in range(1, len(values))])
        
        projections = {}
        current_year = max(years)
        last_value = historical_data[current_year]
        
        for i in range(1, 4):  # 3 year projection
            projections[current_year + i] = int(last_value + (avg_growth * i))
        
        return projections
    
    def _get_industry_trends(self, job_title: str) -> Dict[str, Any]:
        """Get industry trends"""
        return {
            'demand_trend': 'Increasing',
            'supply_trend': 'Tight market',
            'factors': [
                'Digital transformation driving demand',
                'Remote work expanding talent pool',
                'AI/ML skills commanding premium'
            ]
        }
    
    def _get_growth_factors(self, job_title: str) -> List[str]:
        """Get factors affecting salary growth"""
        return [
            'Market demand for role',
            'Technology adoption rate',
            'Industry growth rate',
            'Geographic location trends',
            'Skill scarcity'
        ]
    
    def _get_col_explanation(self, from_loc: str, to_loc: str, factor: float) -> str:
        """Get cost of living explanation"""
        if factor > 1.1:
            return f"{to_loc} has a {round((factor - 1) * 100)}% higher cost of living than {from_loc}"
        elif factor < 0.9:
            return f"{to_loc} has a {round((1 - factor) * 100)}% lower cost of living than {from_loc}"
        else:
            return f"{to_loc} has a similar cost of living to {from_loc}"


# Example usage
if __name__ == '__main__':
    service = SalaryTransparencyService()
    
    # Test salary insights
    print("Testing Salary Insights:")
    result = service.get_salary_insights(
        job_title='Software Engineer',
        location='San Francisco',
        years_experience=3
    )
    print(f"Median salary: ${result['statistics']['base_salary']['median']:,.0f}")
