"""
Company Reviews & Ratings Service
Employee and candidate reviews with workplace insights

Features:
- Submit company reviews (employee/intern/candidate)
- Rate interview experiences
- Workplace culture insights
- Diversity & inclusion ratings
- Work-life balance scores
- Compensation satisfaction
- Career growth opportunities
- Management quality ratings
- Anonymous review posting
- Employer response system
- Review verification
- Company reputation scores

Revenue Model:
- Free for students/employees
- Employer reputation management: $3,000-8,000/year
- Premium employer profiles: $1,000/year
- Review analytics dashboard: $500/month
Target: $100,000+ annually
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
import statistics
import re

from models import db, User, Company
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


class CompanyReviewService:
    """Service for company reviews and ratings"""
    
    # Review categories and rating dimensions
    RATING_CATEGORIES = {
        'overall': {'label': 'Overall Rating', 'weight': 1.0},
        'culture': {'label': 'Company Culture', 'weight': 0.2},
        'compensation': {'label': 'Compensation & Benefits', 'weight': 0.2},
        'work_life_balance': {'label': 'Work-Life Balance', 'weight': 0.2},
        'management': {'label': 'Management Quality', 'weight': 0.15},
        'career_growth': {'label': 'Career Growth', 'weight': 0.15},
        'diversity': {'label': 'Diversity & Inclusion', 'weight': 0.1}
    }
    
    # Review types
    REVIEW_TYPES = [
        'current_employee',
        'former_employee',
        'intern',
        'contractor',
        'candidate',
        'rejected_candidate'
    ]
    
    # Interview difficulty ratings
    INTERVIEW_DIFFICULTY = {
        1: 'Very Easy',
        2: 'Easy',
        3: 'Average',
        4: 'Difficult',
        5: 'Very Difficult'
    }
    
    # Department categories
    DEPARTMENTS = [
        'Engineering',
        'Product',
        'Design',
        'Marketing',
        'Sales',
        'HR',
        'Finance',
        'Operations',
        'Customer Success',
        'Legal',
        'Other'
    ]

    def __init__(self):
        """Initialize company review service"""
        self.logger = logger
    
    def submit_company_review(
        self,
        user_id: int,
        company_id: int,
        review_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a company review
        
        Args:
            user_id: User submitting review
            company_id: Company being reviewed
            review_data: Review content and ratings
        
        Returns:
            Review submission confirmation
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'error': 'Company not found'}
            
            # Check for duplicate reviews
            existing_review = self._check_duplicate_review(user_id, company_id)
            if existing_review and not review_data.get('is_update'):
                return {
                    'success': False,
                    'error': 'You have already reviewed this company',
                    'existing_review_id': existing_review['review_id'],
                    'can_update': True
                }
            
            # Validate review data
            validation = self._validate_review_data(review_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Invalid review data',
                    'validation_errors': validation['errors']
                }
            
            # Create review record
            review_record = {
                'user_id': None if review_data.get('anonymous', True) else user_id,
                'company_id': company_id,
                'reviewer_type': review_data['reviewer_type'],
                'employment_status': review_data.get('employment_status'),
                'position_title': review_data.get('position_title'),
                'department': review_data.get('department'),
                'location': review_data.get('location'),
                'employment_duration': review_data.get('employment_duration'),
                
                # Ratings (1-5 scale)
                'overall_rating': review_data['overall_rating'],
                'culture_rating': review_data.get('culture_rating'),
                'compensation_rating': review_data.get('compensation_rating'),
                'work_life_balance_rating': review_data.get('work_life_balance_rating'),
                'management_rating': review_data.get('management_rating'),
                'career_growth_rating': review_data.get('career_growth_rating'),
                'diversity_rating': review_data.get('diversity_rating'),
                
                # Review content
                'title': review_data.get('title'),
                'pros': review_data.get('pros'),
                'cons': review_data.get('cons'),
                'advice_to_management': review_data.get('advice_to_management'),
                'would_recommend': review_data.get('would_recommend', True),
                
                # Metadata
                'anonymous': review_data.get('anonymous', True),
                'verified': self._verify_employment(user, company, review_data),
                'submitted_at': datetime.utcnow(),
                'helpful_count': 0,
                'report_count': 0,
                'status': 'pending_moderation'
            }
            
            # Content moderation
            moderation = self._moderate_review_content(review_record)
            if not moderation['approved']:
                return {
                    'success': False,
                    'error': 'Review contains inappropriate content',
                    'reasons': moderation['reasons']
                }
            
            review_record['status'] = 'published'
            
            # Save review
            review_id = self._save_company_review(review_record)
            
            # Update company ratings
            self._update_company_ratings(company_id)
            
            # Send confirmation
            self._send_review_confirmation(user, company, review_record)
            
            return {
                'success': True,
                'review_id': review_id,
                'status': 'published',
                'anonymous': review_record['anonymous'],
                'verified': review_record['verified'],
                'message': 'Thank you for your review! Your insights help others make informed decisions.',
                'impact': self._estimate_review_impact(company_id),
                'badges_earned': self._check_reviewer_badges(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting review: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def submit_interview_review(
        self,
        user_id: int,
        company_id: int,
        interview_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit an interview experience review
        
        Args:
            user_id: User submitting review
            company_id: Company being reviewed
            interview_data: Interview experience details
        
        Returns:
            Interview review confirmation
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'error': 'Company not found'}
            
            # Create interview review
            interview_review = {
                'user_id': None if interview_data.get('anonymous', True) else user_id,
                'company_id': company_id,
                'position_applied': interview_data['position_applied'],
                'application_method': interview_data.get('application_method'),
                'interview_date': interview_data.get('interview_date'),
                
                # Interview process
                'process_duration_days': interview_data.get('process_duration_days'),
                'number_of_rounds': interview_data.get('number_of_rounds', 1),
                'interview_types': interview_data.get('interview_types', []),  # ['phone', 'video', 'onsite', 'technical', 'behavioral']
                
                # Experience ratings
                'overall_experience': interview_data['overall_experience'],  # 1-5
                'difficulty_rating': interview_data.get('difficulty_rating', 3),  # 1-5
                'interviewer_professionalism': interview_data.get('interviewer_professionalism', 5),
                'process_transparency': interview_data.get('process_transparency', 5),
                
                # Outcome
                'got_offer': interview_data.get('got_offer', False),
                'offer_accepted': interview_data.get('offer_accepted', False),
                'rejection_feedback': interview_data.get('rejection_feedback', False),
                
                # Details
                'description': interview_data.get('description'),
                'questions_asked': interview_data.get('questions_asked', []),
                'preparation_tips': interview_data.get('preparation_tips'),
                
                # Metadata
                'anonymous': interview_data.get('anonymous', True),
                'submitted_at': datetime.utcnow(),
                'helpful_count': 0,
                'status': 'published'
            }
            
            # Save interview review
            review_id = self._save_interview_review(interview_review)
            
            # Update company interview stats
            self._update_company_interview_stats(company_id)
            
            return {
                'success': True,
                'interview_review_id': review_id,
                'status': 'published',
                'message': 'Thank you for sharing your interview experience!',
                'helps_candidates': self._estimate_interview_review_impact(company_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting interview review: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_company_reviews(
        self,
        company_id: int,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get company reviews with filters and aggregations
        
        Args:
            company_id: Company ID
            filters: Optional filters (reviewer_type, department, rating_range)
        
        Returns:
            Company reviews and aggregated insights
        """
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'error': 'Company not found'}
            
            # Get reviews
            reviews = self._query_company_reviews(company_id, filters)
            
            if not reviews:
                return {
                    'success': True,
                    'company_id': company_id,
                    'company_name': company.name,
                    'total_reviews': 0,
                    'reviews': [],
                    'message': 'Be the first to review this company!'
                }
            
            # Calculate aggregate statistics
            stats = self._calculate_review_statistics(reviews)
            
            # Group by category
            by_reviewer_type = self._group_by_reviewer_type(reviews)
            by_department = self._group_by_department(reviews)
            
            # Extract insights
            insights = self._extract_company_insights(reviews)
            
            # Get rating distribution
            rating_distribution = self._get_rating_distribution(reviews)
            
            # Trending topics
            trending = self._analyze_trending_topics(reviews)
            
            # Format reviews for display
            formatted_reviews = []
            for review in reviews[:20]:  # Top 20 most helpful
                formatted_reviews.append(self._format_review_for_display(review))
            
            return {
                'success': True,
                'company_id': company_id,
                'company_name': company.name,
                'total_reviews': len(reviews),
                'statistics': stats,
                'by_reviewer_type': by_reviewer_type,
                'by_department': by_department,
                'rating_distribution': rating_distribution,
                'insights': insights,
                'trending_topics': trending,
                'reviews': formatted_reviews,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting reviews: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_interview_insights(
        self,
        company_id: int
    ) -> Dict[str, Any]:
        """
        Get company interview insights
        
        Args:
            company_id: Company ID
        
        Returns:
            Interview process insights and statistics
        """
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'error': 'Company not found'}
            
            # Get interview reviews
            interviews = self._query_interview_reviews(company_id)
            
            if not interviews:
                return {
                    'success': True,
                    'company_id': company_id,
                    'data_available': False,
                    'message': 'No interview data available yet'
                }
            
            # Calculate statistics
            stats = {
                'total_interviews': len(interviews),
                'avg_difficulty': round(statistics.mean([i['difficulty_rating'] for i in interviews]), 1),
                'avg_experience_rating': round(statistics.mean([i['overall_experience'] for i in interviews]), 1),
                'avg_process_duration': round(statistics.mean([i['process_duration_days'] for i in interviews if i.get('process_duration_days')]), 1) if any(i.get('process_duration_days') for i in interviews) else None,
                'avg_interview_rounds': round(statistics.mean([i['number_of_rounds'] for i in interviews]), 1),
                'offer_rate': round(sum(1 for i in interviews if i.get('got_offer')) / len(interviews) * 100, 1),
                'acceptance_rate': round(sum(1 for i in interviews if i.get('offer_accepted')) / sum(1 for i in interviews if i.get('got_offer')) * 100, 1) if any(i.get('got_offer') for i in interviews) else 0
            }
            
            # Common interview types
            interview_types = defaultdict(int)
            for interview in interviews:
                for itype in interview.get('interview_types', []):
                    interview_types[itype] += 1
            
            # Common questions
            common_questions = self._extract_common_questions(interviews)
            
            # Preparation tips
            tips = self._aggregate_preparation_tips(interviews)
            
            # Process breakdown
            process_breakdown = self._analyze_interview_process(interviews)
            
            return {
                'success': True,
                'data_available': True,
                'company_id': company_id,
                'company_name': company.name,
                'statistics': stats,
                'difficulty_rating': self.INTERVIEW_DIFFICULTY[round(stats['avg_difficulty'])],
                'common_interview_types': dict(sorted(interview_types.items(), key=lambda x: x[1], reverse=True)),
                'common_questions': common_questions[:10],
                'preparation_tips': tips[:5],
                'process_breakdown': process_breakdown,
                'candidate_feedback': self._get_candidate_feedback_themes(interviews)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting interview insights: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def mark_review_helpful(
        self,
        user_id: int,
        review_id: str
    ) -> Dict[str, Any]:
        """
        Mark a review as helpful
        
        Args:
            user_id: User marking as helpful
            review_id: Review ID
        
        Returns:
            Updated helpful count
        """
        try:
            # Record helpful vote
            vote_recorded = self._record_helpful_vote(user_id, review_id)
            
            if not vote_recorded:
                return {
                    'success': False,
                    'error': 'Already marked as helpful'
                }
            
            # Increment count
            new_count = self._increment_helpful_count(review_id)
            
            # Award reviewer karma
            self._award_reviewer_karma(review_id, 'helpful_vote')
            
            return {
                'success': True,
                'review_id': review_id,
                'helpful_count': new_count
            }
            
        except Exception as e:
            self.logger.error(f"Error marking review helpful: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_company_reputation_score(
        self,
        company_id: int
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive company reputation score
        
        Args:
            company_id: Company ID
        
        Returns:
            Reputation score and breakdown
        """
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'error': 'Company not found'}
            
            # Get all reviews
            reviews = self._query_company_reviews(company_id)
            interviews = self._query_interview_reviews(company_id)
            
            if not reviews and not interviews:
                return {
                    'success': True,
                    'company_id': company_id,
                    'reputation_score': None,
                    'message': 'Insufficient data for reputation score'
                }
            
            # Calculate component scores (0-100 scale)
            scores = {}
            
            # Employee satisfaction (from reviews)
            if reviews:
                scores['employee_satisfaction'] = self._calculate_satisfaction_score(reviews)
                scores['culture_score'] = self._calculate_category_score(reviews, 'culture_rating')
                scores['compensation_score'] = self._calculate_category_score(reviews, 'compensation_rating')
                scores['work_life_balance_score'] = self._calculate_category_score(reviews, 'work_life_balance_rating')
                scores['career_growth_score'] = self._calculate_category_score(reviews, 'career_growth_rating')
                scores['diversity_score'] = self._calculate_category_score(reviews, 'diversity_rating')
            
            # Interview experience (from interview reviews)
            if interviews:
                scores['interview_experience_score'] = self._calculate_interview_score(interviews)
            
            # Calculate weighted reputation score
            reputation_score = self._calculate_weighted_reputation_score(scores)
            
            # Determine reputation tier
            tier = self._get_reputation_tier(reputation_score)
            
            # Get comparison to industry
            industry_comparison = self._compare_to_industry(company, reputation_score)
            
            return {
                'success': True,
                'company_id': company_id,
                'company_name': company.name,
                'reputation_score': reputation_score,
                'reputation_tier': tier,
                'component_scores': scores,
                'industry_comparison': industry_comparison,
                'strengths': self._identify_strengths(scores),
                'improvement_areas': self._identify_improvement_areas(scores),
                'last_calculated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating reputation score: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def respond_to_review(
        self,
        company_admin_id: int,
        review_id: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Company responds to a review (employer branding)
        
        Args:
            company_admin_id: Company administrator user ID
            review_id: Review to respond to
            response: Response message
        
        Returns:
            Response confirmation
        """
        try:
            # Verify company admin
            admin = User.query.get(company_admin_id)
            if not admin or not hasattr(admin, 'is_company_admin'):
                return {'success': False, 'error': 'Unauthorized'}
            
            # Get review
            review = self._get_review(review_id)
            if not review:
                return {'success': False, 'error': 'Review not found'}
            
            # Create response
            response_record = {
                'review_id': review_id,
                'responder_id': company_admin_id,
                'responder_name': admin.name,
                'responder_title': getattr(admin, 'job_title', 'Company Representative'),
                'response': response,
                'responded_at': datetime.utcnow(),
                'status': 'published'
            }
            
            # Save response
            response_id = self._save_review_response(response_record)
            
            # Notify reviewer
            if review.get('user_id'):
                self._notify_reviewer_of_response(review['user_id'], response_record)
            
            return {
                'success': True,
                'response_id': response_id,
                'message': 'Response published successfully',
                'best_practices': [
                    'Thank the reviewer for feedback',
                    'Address specific concerns raised',
                    'Highlight improvements made',
                    'Stay professional and constructive'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error responding to review: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _check_duplicate_review(self, user_id: int, company_id: int) -> Optional[Dict]:
        """Check for duplicate review"""
        # Would query database
        return None
    
    def _validate_review_data(self, data: Dict) -> Dict[str, Any]:
        """Validate review data"""
        errors = []
        
        if 'reviewer_type' not in data or data['reviewer_type'] not in self.REVIEW_TYPES:
            errors.append('Invalid reviewer type')
        
        if 'overall_rating' not in data or not (1 <= data['overall_rating'] <= 5):
            errors.append('Overall rating must be between 1 and 5')
        
        if not data.get('pros') and not data.get('cons'):
            errors.append('Must provide pros or cons')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _verify_employment(self, user: User, company: Company, review_data: Dict) -> bool:
        """Verify employment relationship"""
        # Check if user's email domain matches company
        if user.email and company.domain:
            if user.email.endswith(f'@{company.domain}'):
                return True
        
        # Check if user has job history with company
        # Would check user's experience records
        return False
    
    def _moderate_review_content(self, review: Dict) -> Dict[str, Any]:
        """Moderate review content for inappropriate material"""
        flagged_words = ['scam', 'illegal', 'lawsuit']  # Simplified
        
        text = f"{review.get('title', '')} {review.get('pros', '')} {review.get('cons', '')}"
        
        reasons = []
        for word in flagged_words:
            if word in text.lower():
                reasons.append(f"Contains potentially inappropriate word: {word}")
        
        return {
            'approved': len(reasons) == 0,
            'reasons': reasons
        }
    
    def _save_company_review(self, review: Dict) -> str:
        """Save company review"""
        review_id = f"review_{review['company_id']}_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved company review: {review_id}")
        return review_id
    
    def _update_company_ratings(self, company_id: int):
        """Update company aggregate ratings"""
        self.logger.info(f"Updated ratings for company {company_id}")
    
    def _send_review_confirmation(self, user: User, company: Company, review: Dict):
        """Send review confirmation email"""
        self.logger.info(f"Sent review confirmation to {user.email}")
    
    def _estimate_review_impact(self, company_id: int) -> str:
        """Estimate review impact"""
        return "Your review will help 100+ candidates make informed decisions"
    
    def _check_reviewer_badges(self, user_id: int) -> List[str]:
        """Check for reviewer achievement badges"""
        return ['First Reviewer', 'Helpful Contributor']
    
    def _save_interview_review(self, review: Dict) -> str:
        """Save interview review"""
        review_id = f"interview_{review['company_id']}_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved interview review: {review_id}")
        return review_id
    
    def _update_company_interview_stats(self, company_id: int):
        """Update company interview statistics"""
        self.logger.info(f"Updated interview stats for company {company_id}")
    
    def _estimate_interview_review_impact(self, company_id: int) -> str:
        """Estimate interview review impact"""
        return "Your insights will help 50+ candidates prepare better"
    
    def _query_company_reviews(self, company_id: int, filters: Dict = None) -> List[Dict]:
        """Query company reviews"""
        # Simulated review data
        reviews = []
        for i in range(20):
            reviews.append({
                'review_id': f'review_{i}',
                'company_id': company_id,
                'reviewer_type': 'current_employee',
                'overall_rating': 3 + (i % 3),
                'culture_rating': 4,
                'compensation_rating': 3,
                'work_life_balance_rating': 4,
                'management_rating': 3,
                'career_growth_rating': 4,
                'diversity_rating': 4,
                'title': f'Review Title {i}',
                'pros': 'Great culture, good benefits',
                'cons': 'Long hours sometimes',
                'would_recommend': True,
                'submitted_at': datetime.utcnow() - timedelta(days=i*10),
                'helpful_count': i * 2
            })
        return reviews
    
    def _calculate_review_statistics(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate review statistics"""
        stats = {}
        
        for category, config in self.RATING_CATEGORIES.items():
            if category == 'overall':
                ratings = [r['overall_rating'] for r in reviews]
            else:
                rating_key = f'{category}_rating'
                ratings = [r[rating_key] for r in reviews if r.get(rating_key)]
            
            if ratings:
                stats[category] = {
                    'average': round(statistics.mean(ratings), 1),
                    'count': len(ratings),
                    'distribution': self._get_distribution(ratings)
                }
        
        stats['would_recommend_percentage'] = round(
            sum(1 for r in reviews if r.get('would_recommend')) / len(reviews) * 100,
            1
        )
        
        return stats
    
    def _get_distribution(self, ratings: List[int]) -> Dict[int, int]:
        """Get rating distribution"""
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            dist[int(rating)] += 1
        return dist
    
    def _group_by_reviewer_type(self, reviews: List[Dict]) -> Dict[str, Dict]:
        """Group reviews by reviewer type"""
        grouped = defaultdict(list)
        for review in reviews:
            grouped[review['reviewer_type']].append(review['overall_rating'])
        
        result = {}
        for rtype, ratings in grouped.items():
            result[rtype] = {
                'count': len(ratings),
                'avg_rating': round(statistics.mean(ratings), 1)
            }
        return result
    
    def _group_by_department(self, reviews: List[Dict]) -> Dict[str, Dict]:
        """Group reviews by department"""
        grouped = defaultdict(list)
        for review in reviews:
            dept = review.get('department', 'Unknown')
            grouped[dept].append(review['overall_rating'])
        
        result = {}
        for dept, ratings in grouped.items():
            result[dept] = {
                'count': len(ratings),
                'avg_rating': round(statistics.mean(ratings), 1)
            }
        return result
    
    def _extract_company_insights(self, reviews: List[Dict]) -> List[str]:
        """Extract key insights from reviews"""
        insights = []
        
        # Most common pros/cons
        pros_text = ' '.join([r.get('pros', '') for r in reviews])
        if 'culture' in pros_text.lower():
            insights.append('Employees frequently praise company culture')
        
        cons_text = ' '.join([r.get('cons', '') for r in reviews])
        if 'hours' in cons_text.lower() or 'balance' in cons_text.lower():
            insights.append('Work-life balance mentioned as area for improvement')
        
        # Recommendation rate
        recommend_pct = sum(1 for r in reviews if r.get('would_recommend')) / len(reviews) * 100
        if recommend_pct > 80:
            insights.append(f'{int(recommend_pct)}% of employees would recommend this company')
        
        return insights[:5]
    
    def _get_rating_distribution(self, reviews: List[Dict]) -> Dict[str, int]:
        """Get overall rating distribution"""
        ratings = [r['overall_rating'] for r in reviews]
        return self._get_distribution(ratings)
    
    def _analyze_trending_topics(self, reviews: List[Dict]) -> List[Dict]:
        """Analyze trending topics in reviews"""
        return [
            {'topic': 'Remote Work', 'mentions': 15, 'sentiment': 'positive'},
            {'topic': 'Career Growth', 'mentions': 12, 'sentiment': 'mixed'},
            {'topic': 'Team Culture', 'mentions': 10, 'sentiment': 'positive'}
        ]
    
    def _format_review_for_display(self, review: Dict) -> Dict:
        """Format review for display"""
        return {
            'review_id': review['review_id'],
            'reviewer_type': review['reviewer_type'],
            'overall_rating': review['overall_rating'],
            'title': review['title'],
            'pros': review['pros'],
            'cons': review['cons'],
            'would_recommend': review.get('would_recommend'),
            'submitted_at': review['submitted_at'].isoformat() if isinstance(review['submitted_at'], datetime) else review['submitted_at'],
            'helpful_count': review.get('helpful_count', 0),
            'verified': review.get('verified', False)
        }
    
    def _query_interview_reviews(self, company_id: int) -> List[Dict]:
        """Query interview reviews"""
        # Simulated data
        interviews = []
        for i in range(15):
            interviews.append({
                'company_id': company_id,
                'position_applied': 'Software Engineer',
                'overall_experience': 3 + (i % 3),
                'difficulty_rating': 3 + (i % 3),
                'number_of_rounds': 3,
                'process_duration_days': 14 + (i % 10),
                'interview_types': ['phone', 'technical', 'onsite'],
                'got_offer': i % 3 == 0,
                'offer_accepted': i % 6 == 0,
                'questions_asked': ['Tell me about yourself', 'Technical coding question'],
                'preparation_tips': 'Review data structures'
            })
        return interviews
    
    def _extract_common_questions(self, interviews: List[Dict]) -> List[str]:
        """Extract common interview questions"""
        all_questions = []
        for interview in interviews:
            all_questions.extend(interview.get('questions_asked', []))
        
        # Count frequency (simplified)
        return list(set(all_questions))[:10]
    
    def _aggregate_preparation_tips(self, interviews: List[Dict]) -> List[str]:
        """Aggregate preparation tips"""
        tips = [i.get('preparation_tips') for i in interviews if i.get('preparation_tips')]
        return list(set(tips))[:5]
    
    def _analyze_interview_process(self, interviews: List[Dict]) -> Dict[str, Any]:
        """Analyze interview process"""
        return {
            'typical_rounds': 3,
            'typical_duration': '2-3 weeks',
            'stages': ['Phone Screen', 'Technical Interview', 'Onsite/Final Round']
        }
    
    def _get_candidate_feedback_themes(self, interviews: List[Dict]) -> List[str]:
        """Get common feedback themes"""
        return [
            'Interviewers were professional and friendly',
            'Technical questions were challenging but fair',
            'Process took longer than expected'
        ]
    
    def _record_helpful_vote(self, user_id: int, review_id: str) -> bool:
        """Record helpful vote"""
        # Would check if already voted
        return True
    
    def _increment_helpful_count(self, review_id: str) -> int:
        """Increment helpful count"""
        try:
            from models_extended import CompanyReview
            
            review = CompanyReview.query.filter_by(review_id=review_id).first()
            if review:
                review.helpful_count = (review.helpful_count or 0) + 1
                db.session.commit()
                return review.helpful_count
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error incrementing helpful count: {e}")
            return 1
    
    def _award_reviewer_karma(self, review_id: str, action: str):
        """Award karma to reviewer"""
        self.logger.info(f"Awarded karma for {action}")
    
    def _calculate_satisfaction_score(self, reviews: List[Dict]) -> int:
        """Calculate employee satisfaction score (0-100)"""
        avg_rating = statistics.mean([r['overall_rating'] for r in reviews])
        return int((avg_rating / 5.0) * 100)
    
    def _calculate_category_score(self, reviews: List[Dict], category: str) -> int:
        """Calculate category score"""
        ratings = [r[category] for r in reviews if r.get(category)]
        if not ratings:
            return None
        avg_rating = statistics.mean(ratings)
        return int((avg_rating / 5.0) * 100)
    
    def _calculate_interview_score(self, interviews: List[Dict]) -> int:
        """Calculate interview experience score"""
        avg_experience = statistics.mean([i['overall_experience'] for i in interviews])
        return int((avg_experience / 5.0) * 100)
    
    def _calculate_weighted_reputation_score(self, scores: Dict[str, int]) -> int:
        """Calculate weighted reputation score"""
        if not scores:
            return 0
        
        # Simple average for now
        valid_scores = [v for v in scores.values() if v is not None]
        return int(statistics.mean(valid_scores)) if valid_scores else 0
    
    def _get_reputation_tier(self, score: int) -> str:
        """Get reputation tier from score"""
        if score >= 90:
            return 'Exceptional'
        elif score >= 75:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 45:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def _compare_to_industry(self, company: Company, score: int) -> Dict[str, Any]:
        """Compare to industry average"""
        try:
            from models_extended import CompanyReview
            
            # Calculate industry average from all companies in same industry
            industry_reviews = CompanyReview.query.join(Company).filter(
                Company.industry == company.industry
            ).all()
            
            if industry_reviews:
                industry_avg = statistics.mean([r.overall_rating * 20 for r in industry_reviews])
            else:
                industry_avg = 72  # Default if no data
            
        except Exception as e:
            self.logger.error(f"Error calculating industry average: {e}")
            industry_avg = 72
        
        return {
            'industry': getattr(company, 'industry', 'Technology'),
            'industry_average': industry_avg,
            'difference': score - industry_avg,
            'percentile': 65
        }
    
    def _identify_strengths(self, scores: Dict[str, int]) -> List[str]:
        """Identify company strengths"""
        strengths = []
        for category, score in scores.items():
            if score and score >= 80:
                strengths.append(category.replace('_', ' ').title())
        return strengths[:3]
    
    def _identify_improvement_areas(self, scores: Dict[str, int]) -> List[str]:
        """Identify improvement areas"""
        areas = []
        for category, score in scores.items():
            if score and score < 60:
                areas.append(category.replace('_', ' ').title())
        return areas[:3]
    
    def _get_review(self, review_id: str) -> Optional[Dict]:
        """Get review by ID"""
        return {
            'review_id': review_id,
            'company_id': 1,
            'user_id': 1
        }
    
    def _save_review_response(self, response: Dict) -> str:
        """Save review response"""
        response_id = f"response_{response['review_id']}_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved review response: {response_id}")
        return response_id
    
    def _notify_reviewer_of_response(self, user_id: int, response: Dict):
        """Notify reviewer of company response"""
        self.logger.info(f"Notified user {user_id} of company response")


# Example usage
if __name__ == '__main__':
    service = CompanyReviewService()
    
    # Test company reviews
    print("Testing Company Reviews:")
    result = service.get_company_reviews(company_id=1)
    print(f"Total reviews: {result['total_reviews']}")
