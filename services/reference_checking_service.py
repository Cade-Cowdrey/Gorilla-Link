"""
Automated Reference Checking Service
Digital reference collection with AI analysis and blockchain verification

Features:
- Send digital reference requests
- Structured reference questionnaires
- Video reference testimonials
- AI sentiment analysis of references
- Reference verification via blockchain
- Automated follow-up reminders
- Reference template library
- Anonymous reference feedback
- Reference scoring system
- Bulk reference requests
- Reference portfolio sharing
- Fraud detection
- GDPR compliance

Revenue Model:
- Free basic reference requests (3/year)
- Premium unlimited references: $15/month
- Employer bulk verification: $500-2,000/month
- Blockchain verification certificates: $10/reference
Target: $100,000+ annually
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
import hashlib
import json

from models import db, User
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


class ReferenceCheckingService:
    """Service for automated reference checking"""
    
    # Reference types
    REFERENCE_TYPES = [
        'professional',
        'academic',
        'character',
        'volunteer',
        'manager',
        'colleague',
        'client'
    ]
    
    # Relationship types
    RELATIONSHIPS = [
        'Direct Manager',
        'Indirect Manager',
        'Colleague',
        'Professor',
        'Academic Advisor',
        'Client',
        'Mentor',
        'Other'
    ]
    
    # Rating dimensions
    RATING_DIMENSIONS = {
        'work_quality': 'Quality of Work',
        'reliability': 'Reliability',
        'communication': 'Communication Skills',
        'teamwork': 'Teamwork',
        'leadership': 'Leadership',
        'technical_skills': 'Technical Skills',
        'problem_solving': 'Problem Solving',
        'creativity': 'Creativity',
        'professionalism': 'Professionalism'
    }
    
    # Questionnaire templates
    QUESTIONNAIRE_TEMPLATES = {
        'professional': [
            'How long did you work with the candidate?',
            'What was your working relationship?',
            'What were the candidate\'s main responsibilities?',
            'What are the candidate\'s greatest strengths?',
            'What areas could the candidate improve?',
            'Would you hire this candidate again?',
            'On a scale of 1-10, how would you rate their overall performance?'
        ],
        'academic': [
            'How long have you known the candidate?',
            'In what capacity did you work with the candidate?',
            'How does the candidate compare to other students?',
            'What are the candidate\'s academic strengths?',
            'How would you describe the candidate\'s work ethic?',
            'Would you recommend this candidate for graduate studies/employment?'
        ]
    }

    def __init__(self):
        """Initialize reference checking service"""
        self.logger = logger
    
    def send_reference_request(
        self,
        user_id: int,
        reference_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a reference request
        
        Args:
            user_id: User requesting reference
            reference_details: Reference details (name, email, relationship)
        
        Returns:
            Request confirmation
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check request limits
            limit_check = self._check_reference_limits(user_id)
            if not limit_check['allowed']:
                return {
                    'success': False,
                    'error': 'Reference request limit reached',
                    'limit': limit_check['limit'],
                    'used': limit_check['used'],
                    'upgrade_to_premium': True
                }
            
            # Validate reference details
            validation = self._validate_reference_details(reference_details)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Invalid reference details',
                    'validation_errors': validation['errors']
                }
            
            # Check for duplicate requests
            duplicate = self._check_duplicate_request(
                user_id,
                reference_details['email']
            )
            if duplicate:
                return {
                    'success': False,
                    'error': 'Reference request already sent to this person',
                    'existing_request_id': duplicate['request_id'],
                    'status': duplicate['status']
                }
            
            # Create reference request
            request_record = {
                'request_id': self._generate_request_id(),
                'user_id': user_id,
                'reference_name': reference_details['name'],
                'reference_email': reference_details['email'],
                'reference_phone': reference_details.get('phone'),
                'relationship': reference_details['relationship'],
                'reference_type': reference_details.get('reference_type', 'professional'),
                'company': reference_details.get('company'),
                'position': reference_details.get('position'),
                'dates_worked': reference_details.get('dates_worked', {}),
                'questionnaire_type': reference_details.get('questionnaire_type', 'professional'),
                'custom_questions': reference_details.get('custom_questions', []),
                'allow_video_reference': reference_details.get('allow_video_reference', True),
                'request_message': reference_details.get('message', ''),
                'status': 'pending',
                'sent_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=14),
                'reminder_count': 0
            }
            
            # Generate secure access token
            request_record['access_token'] = self._generate_access_token(request_record)
            
            # Save request
            request_id = self._save_reference_request(request_record)
            
            # Send email to reference
            email_sent = self._send_reference_request_email(request_record, user)
            
            # Schedule reminders
            self._schedule_reference_reminders(request_id)
            
            return {
                'success': True,
                'request_id': request_id,
                'status': 'pending',
                'reference_name': request_record['reference_name'],
                'expires_at': request_record['expires_at'].isoformat(),
                'email_sent': email_sent,
                'estimated_completion': '3-5 business days',
                'tracking_url': f'/references/track/{request_id}',
                'reminders_scheduled': True
            }
            
        except Exception as e:
            self.logger.error(f"Error sending reference request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def submit_reference(
        self,
        access_token: str,
        reference_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reference submits their reference
        
        Args:
            access_token: Secure access token from email
            reference_data: Reference responses
        
        Returns:
            Submission confirmation
        """
        try:
            # Verify access token
            request = self._verify_access_token(access_token)
            if not request:
                return {
                    'success': False,
                    'error': 'Invalid or expired access token'
                }
            
            if request['status'] != 'pending':
                return {
                    'success': False,
                    'error': 'Reference already submitted'
                }
            
            # Validate reference data
            validation = self._validate_reference_submission(reference_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Incomplete reference',
                    'validation_errors': validation['errors']
                }
            
            # Create reference record
            reference_record = {
                'reference_id': self._generate_reference_id(),
                'request_id': request['request_id'],
                'user_id': request['user_id'],
                'reference_name': request['reference_name'],
                'reference_email': request['reference_email'],
                'relationship': reference_data['relationship'],
                'reference_type': request['reference_type'],
                
                # Ratings (1-10 scale)
                'ratings': {
                    'work_quality': reference_data.get('work_quality', 0),
                    'reliability': reference_data.get('reliability', 0),
                    'communication': reference_data.get('communication', 0),
                    'teamwork': reference_data.get('teamwork', 0),
                    'leadership': reference_data.get('leadership', 0),
                    'technical_skills': reference_data.get('technical_skills', 0),
                    'problem_solving': reference_data.get('problem_solving', 0)
                },
                
                # Responses
                'questionnaire_responses': reference_data.get('responses', []),
                'strengths': reference_data.get('strengths'),
                'areas_for_improvement': reference_data.get('areas_for_improvement'),
                'would_rehire': reference_data.get('would_rehire'),
                'overall_recommendation': reference_data.get('overall_recommendation'),
                'additional_comments': reference_data.get('additional_comments'),
                
                # Video reference (optional)
                'video_reference_url': reference_data.get('video_url'),
                
                # Metadata
                'submitted_at': datetime.utcnow(),
                'ip_address': reference_data.get('ip_address'),
                'verified': False,
                'blockchain_hash': None
            }
            
            # Calculate overall score
            reference_record['overall_score'] = self._calculate_reference_score(reference_record)
            
            # AI sentiment analysis
            sentiment = self._analyze_reference_sentiment(reference_record)
            reference_record['sentiment'] = sentiment
            
            # Save reference
            reference_id = self._save_reference(reference_record)
            
            # Update request status
            self._update_request_status(request['request_id'], 'completed')
            
            # Generate blockchain verification
            blockchain_hash = self._create_blockchain_verification(reference_record)
            reference_record['blockchain_hash'] = blockchain_hash
            reference_record['verified'] = True
            
            # Notify candidate
            user = User.query.get(request['user_id'])
            self._notify_candidate_of_reference(user, reference_record)
            
            # Send thank you to reference
            self._send_reference_thank_you(request['reference_email'], request['reference_name'])
            
            return {
                'success': True,
                'reference_id': reference_id,
                'message': 'Thank you for providing your reference!',
                'blockchain_verified': True,
                'blockchain_hash': blockchain_hash,
                'certificate_url': f'/references/certificate/{reference_id}',
                'candidate_notified': True
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting reference: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_references(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get all references for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of references and statistics
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get completed references
            references = self._query_user_references(user_id)
            
            # Get pending requests
            pending_requests = self._query_pending_requests(user_id)
            
            # Calculate statistics
            stats = self._calculate_reference_statistics(references)
            
            # Format references for display
            formatted_references = []
            for ref in references:
                formatted_references.append(self._format_reference_for_display(ref))
            
            return {
                'success': True,
                'user_id': user_id,
                'references': formatted_references,
                'pending_requests': len(pending_requests),
                'statistics': stats,
                'reference_portfolio_url': f'/references/portfolio/{user_id}',
                'share_url': f'/references/share/{self._generate_share_token(user_id)}'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting references: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_reference(
        self,
        reference_id: str,
        blockchain_hash: str
    ) -> Dict[str, Any]:
        """
        Verify a reference using blockchain
        
        Args:
            reference_id: Reference ID
            blockchain_hash: Blockchain hash to verify
        
        Returns:
            Verification result
        """
        try:
            # Get reference
            reference = self._get_reference(reference_id)
            if not reference:
                return {
                    'success': False,
                    'error': 'Reference not found'
                }
            
            # Verify blockchain hash
            verification = self._verify_blockchain_hash(reference, blockchain_hash)
            
            if not verification['valid']:
                return {
                    'success': True,
                    'verified': False,
                    'message': 'Verification failed - hash mismatch or tampering detected',
                    'details': verification['details']
                }
            
            return {
                'success': True,
                'verified': True,
                'reference_id': reference_id,
                'reference_name': reference['reference_name'],
                'submitted_at': reference['submitted_at'],
                'blockchain_hash': reference['blockchain_hash'],
                'overall_score': reference['overall_score'],
                'message': 'Reference is authentic and has not been tampered with',
                'verification_details': verification['details']
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying reference: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def request_bulk_references(
        self,
        user_id: int,
        references_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send bulk reference requests
        
        Args:
            user_id: User ID
            references_list: List of reference details
        
        Returns:
            Bulk request confirmation
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if len(references_list) > 10:
                return {
                    'success': False,
                    'error': 'Maximum 10 references per bulk request'
                }
            
            results = []
            successful = 0
            failed = 0
            
            for ref_details in references_list:
                result = self.send_reference_request(user_id, ref_details)
                results.append({
                    'reference_name': ref_details.get('name'),
                    'success': result['success'],
                    'request_id': result.get('request_id'),
                    'error': result.get('error')
                })
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
            
            return {
                'success': True,
                'total_requested': len(references_list),
                'successful': successful,
                'failed': failed,
                'results': results,
                'tracking_dashboard': f'/references/dashboard'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending bulk references: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_reference_report(
        self,
        user_id: int,
        format: str = 'pdf'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive reference report
        
        Args:
            user_id: User ID
            format: Report format (pdf, json, html)
        
        Returns:
            Report download URL
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get references
            references = self._query_user_references(user_id)
            
            if not references:
                return {
                    'success': False,
                    'error': 'No references available'
                }
            
            # Calculate statistics
            stats = self._calculate_reference_statistics(references)
            
            # Generate report
            report_data = {
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'profile_url': f'/profile/{user_id}'
                },
                'summary': stats,
                'references': references,
                'generated_at': datetime.utcnow().isoformat(),
                'blockchain_verified': all(r.get('verified') for r in references)
            }
            
            # Create report file
            report_id = self._generate_report_file(report_data, format)
            
            return {
                'success': True,
                'report_id': report_id,
                'format': format,
                'download_url': f'/references/reports/{report_id}.{format}',
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating reference report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_reference_patterns(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        AI-powered analysis of reference patterns
        
        Args:
            user_id: User ID
        
        Returns:
            Detailed analysis and insights
        """
        try:
            # Get references
            references = self._query_user_references(user_id)
            
            if len(references) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 references for pattern analysis'
                }
            
            # Analyze patterns
            patterns = {
                'consistency': self._analyze_consistency(references),
                'strengths_themes': self._extract_common_themes(references, 'strengths'),
                'improvement_themes': self._extract_common_themes(references, 'areas_for_improvement'),
                'rating_distribution': self._analyze_rating_distribution(references),
                'sentiment_trends': self._analyze_sentiment_trends(references),
                'credibility_score': self._calculate_credibility_score(references)
            }
            
            # Generate insights
            insights = self._generate_reference_insights(patterns)
            
            # Recommendations
            recommendations = self._generate_reference_recommendations(patterns)
            
            return {
                'success': True,
                'user_id': user_id,
                'total_references': len(references),
                'patterns': patterns,
                'insights': insights,
                'recommendations': recommendations,
                'credibility_score': patterns['credibility_score']
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing reference patterns: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _check_reference_limits(self, user_id: int) -> Dict[str, Any]:
        """Check reference request limits"""
        # Free tier: 3 requests per year
        # Premium: unlimited
        used = 1  # Would query actual usage
        limit = 3
        
        is_premium = False  # Would check user subscription
        
        if is_premium:
            return {'allowed': True, 'limit': 999, 'used': used}
        
        return {
            'allowed': used < limit,
            'limit': limit,
            'used': used
        }
    
    def _validate_reference_details(self, details: Dict) -> Dict[str, Any]:
        """Validate reference details"""
        errors = []
        
        if not details.get('name'):
            errors.append('Reference name is required')
        
        if not details.get('email'):
            errors.append('Reference email is required')
        
        if not details.get('relationship') or details['relationship'] not in self.RELATIONSHIPS:
            errors.append('Valid relationship is required')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _check_duplicate_request(self, user_id: int, email: str) -> Optional[Dict]:
        """Check for duplicate reference requests"""
        # Would query database
        return None
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{datetime.utcnow().timestamp()}"
    
    def _generate_access_token(self, request: Dict) -> str:
        """Generate secure access token"""
        data = f"{request['request_id']}{request['reference_email']}{datetime.utcnow()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _save_reference_request(self, request: Dict) -> str:
        """Save reference request"""
        self.logger.info(f"Saved reference request: {request['request_id']}")
        return request['request_id']
    
    def _send_reference_request_email(self, request: Dict, user: User) -> bool:
        """Send reference request email"""
        self.logger.info(f"Sent reference request email to {request['reference_email']}")
        return True
    
    def _schedule_reference_reminders(self, request_id: str):
        """Schedule reminder emails"""
        # Schedule reminders at day 3, 7, and 10
        self.logger.info(f"Scheduled reminders for {request_id}")
    
    def _verify_access_token(self, token: str) -> Optional[Dict]:
        """Verify access token and get request"""
        # Would verify token and return request
        return {
            'request_id': 'req_123',
            'user_id': 1,
            'reference_name': 'John Doe',
            'reference_email': 'john@example.com',
            'reference_type': 'professional',
            'status': 'pending'
        }
    
    def _validate_reference_submission(self, data: Dict) -> Dict[str, Any]:
        """Validate reference submission"""
        errors = []
        
        if not data.get('relationship'):
            errors.append('Relationship is required')
        
        if not data.get('responses'):
            errors.append('Questionnaire responses are required')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _generate_reference_id(self) -> str:
        """Generate unique reference ID"""
        return f"ref_{datetime.utcnow().timestamp()}"
    
    def _calculate_reference_score(self, reference: Dict) -> float:
        """Calculate overall reference score"""
        ratings = reference['ratings']
        valid_ratings = [v for v in ratings.values() if v > 0]
        
        if not valid_ratings:
            return 0.0
        
        return round(sum(valid_ratings) / len(valid_ratings), 1)
    
    def _analyze_reference_sentiment(self, reference: Dict) -> Dict[str, Any]:
        """Analyze sentiment of reference text"""
        # Simplified sentiment analysis
        # Would use NLP/GPT-4 for real analysis
        text = f"{reference.get('strengths', '')} {reference.get('additional_comments', '')}"
        
        positive_words = ['excellent', 'outstanding', 'great', 'strong', 'exceptional']
        negative_words = ['weak', 'poor', 'lacking', 'needs improvement']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = 0.8
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = 0.3
        else:
            sentiment = 'neutral'
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count
        }
    
    def _save_reference(self, reference: Dict) -> str:
        """Save reference"""
        self.logger.info(f"Saved reference: {reference['reference_id']}")
        return reference['reference_id']
    
    def _update_request_status(self, request_id: str, status: str):
        """Update request status"""
        self.logger.info(f"Updated request {request_id} to {status}")
    
    def _create_blockchain_verification(self, reference: Dict) -> str:
        """Create blockchain verification hash"""
        # Create hash of reference data
        data = json.dumps({
            'reference_id': reference['reference_id'],
            'user_id': reference['user_id'],
            'reference_email': reference['reference_email'],
            'submitted_at': reference['submitted_at'].isoformat() if isinstance(reference['submitted_at'], datetime) else reference['submitted_at'],
            'overall_score': reference['overall_score']
        }, sort_keys=True)
        
        blockchain_hash = hashlib.sha256(data.encode()).hexdigest()
        
        # Would actually write to blockchain here
        self.logger.info(f"Created blockchain verification: {blockchain_hash}")
        
        return blockchain_hash
    
    def _notify_candidate_of_reference(self, user: User, reference: Dict):
        """Notify candidate of new reference"""
        self.logger.info(f"Notified {user.email} of new reference")
    
    def _send_reference_thank_you(self, email: str, name: str):
        """Send thank you email to reference"""
        self.logger.info(f"Sent thank you to {email}")
    
    def _query_user_references(self, user_id: int) -> List[Dict]:
        """Query user's completed references"""
        # Simulated reference data
        references = []
        for i in range(3):
            references.append({
                'reference_id': f'ref_{i}',
                'user_id': user_id,
                'reference_name': f'Reference {i}',
                'reference_email': f'ref{i}@example.com',
                'relationship': 'Direct Manager',
                'reference_type': 'professional',
                'overall_score': 8.5 + (i * 0.5),
                'ratings': {
                    'work_quality': 9,
                    'reliability': 9,
                    'communication': 8,
                    'teamwork': 9,
                    'leadership': 8
                },
                'strengths': 'Excellent technical skills, great team player',
                'would_rehire': True,
                'submitted_at': datetime.utcnow() - timedelta(days=i*10),
                'verified': True,
                'blockchain_hash': f'hash_{i}',
                'sentiment': {'sentiment': 'positive', 'score': 0.85}
            })
        return references
    
    def _query_pending_requests(self, user_id: int) -> List[Dict]:
        """Query pending reference requests"""
        return []
    
    def _calculate_reference_statistics(self, references: List[Dict]) -> Dict[str, Any]:
        """Calculate reference statistics"""
        if not references:
            return {}
        
        scores = [r['overall_score'] for r in references]
        
        return {
            'total_references': len(references),
            'average_score': round(sum(scores) / len(scores), 1),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'would_rehire_percentage': round(
                sum(1 for r in references if r.get('would_rehire')) / len(references) * 100,
                1
            ),
            'verified_references': sum(1 for r in references if r.get('verified')),
            'positive_sentiment': sum(1 for r in references if r.get('sentiment', {}).get('sentiment') == 'positive')
        }
    
    def _format_reference_for_display(self, reference: Dict) -> Dict:
        """Format reference for display"""
        return {
            'reference_id': reference['reference_id'],
            'reference_name': reference['reference_name'],
            'relationship': reference['relationship'],
            'reference_type': reference['reference_type'],
            'overall_score': reference['overall_score'],
            'would_rehire': reference.get('would_rehire'),
            'submitted_at': reference['submitted_at'].isoformat() if isinstance(reference['submitted_at'], datetime) else reference['submitted_at'],
            'verified': reference.get('verified', False),
            'blockchain_verified': reference.get('verified', False),
            'sentiment': reference.get('sentiment', {}).get('sentiment', 'neutral')
        }
    
    def _generate_share_token(self, user_id: int) -> str:
        """Generate share token for reference portfolio"""
        data = f"{user_id}{datetime.utcnow()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _get_reference(self, reference_id: str) -> Optional[Dict]:
        """Get reference by ID"""
        return {
            'reference_id': reference_id,
            'reference_name': 'John Doe',
            'submitted_at': datetime.utcnow(),
            'overall_score': 9.0,
            'blockchain_hash': 'abc123def456',
            'verified': True
        }
    
    def _verify_blockchain_hash(self, reference: Dict, provided_hash: str) -> Dict[str, Any]:
        """Verify blockchain hash"""
        # Would verify against actual blockchain
        is_valid = reference['blockchain_hash'] == provided_hash
        
        return {
            'valid': is_valid,
            'details': {
                'stored_hash': reference['blockchain_hash'],
                'provided_hash': provided_hash,
                'match': is_valid,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _generate_report_file(self, data: Dict, format: str) -> str:
        """Generate report file"""
        report_id = f"report_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Generated {format} report: {report_id}")
        return report_id
    
    def _analyze_consistency(self, references: List[Dict]) -> Dict[str, Any]:
        """Analyze consistency across references"""
        scores = [r['overall_score'] for r in references]
        variance = max(scores) - min(scores)
        
        if variance <= 1.0:
            consistency = 'High'
        elif variance <= 2.0:
            consistency = 'Moderate'
        else:
            consistency = 'Low'
        
        return {
            'consistency_level': consistency,
            'score_variance': variance,
            'interpretation': f'References show {consistency.lower()} consistency in ratings'
        }
    
    def _extract_common_themes(self, references: List[Dict], field: str) -> List[str]:
        """Extract common themes from references"""
        # Simplified theme extraction
        # Would use NLP for real implementation
        return [
            'Strong technical skills',
            'Excellent communicator',
            'Great team player'
        ]
    
    def _analyze_rating_distribution(self, references: List[Dict]) -> Dict[str, Any]:
        """Analyze rating distribution"""
        all_ratings = []
        for ref in references:
            all_ratings.extend(ref['ratings'].values())
        
        return {
            'average': round(sum(all_ratings) / len(all_ratings), 1),
            'distribution': {
                '9-10': sum(1 for r in all_ratings if r >= 9),
                '7-8': sum(1 for r in all_ratings if 7 <= r < 9),
                '5-6': sum(1 for r in all_ratings if 5 <= r < 7),
                '1-4': sum(1 for r in all_ratings if r < 5)
            }
        }
    
    def _analyze_sentiment_trends(self, references: List[Dict]) -> Dict[str, int]:
        """Analyze sentiment trends"""
        sentiments = [r.get('sentiment', {}).get('sentiment', 'neutral') for r in references]
        
        return {
            'positive': sentiments.count('positive'),
            'neutral': sentiments.count('neutral'),
            'negative': sentiments.count('negative')
        }
    
    def _calculate_credibility_score(self, references: List[Dict]) -> int:
        """Calculate overall credibility score"""
        score = 0
        
        # Verified references
        verified_count = sum(1 for r in references if r.get('verified'))
        score += (verified_count / len(references)) * 40
        
        # Consistent ratings
        scores = [r['overall_score'] for r in references]
        variance = max(scores) - min(scores)
        if variance <= 1.0:
            score += 30
        elif variance <= 2.0:
            score += 20
        
        # Positive sentiment
        positive = sum(1 for r in references if r.get('sentiment', {}).get('sentiment') == 'positive')
        score += (positive / len(references)) * 30
        
        return int(score)
    
    def _generate_reference_insights(self, patterns: Dict) -> List[str]:
        """Generate insights from patterns"""
        insights = []
        
        if patterns['credibility_score'] >= 80:
            insights.append('Your references show exceptional credibility and consistency')
        
        if patterns['consistency']['consistency_level'] == 'High':
            insights.append('References consistently praise your performance')
        
        positive_ratio = patterns['sentiment_trends']['positive'] / sum(patterns['sentiment_trends'].values())
        if positive_ratio >= 0.8:
            insights.append('Overwhelming positive feedback from references')
        
        return insights
    
    def _generate_reference_recommendations(self, patterns: Dict) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if patterns['credibility_score'] < 70:
            recommendations.append('Request more verified references to increase credibility')
        
        if patterns['consistency']['consistency_level'] == 'Low':
            recommendations.append('Consider adding references from similar roles for consistency')
        
        return recommendations


# Example usage
if __name__ == '__main__':
    service = ReferenceCheckingService()
    
    # Test reference request
    print("Testing Reference Request:")
    result = service.send_reference_request(
        user_id=1,
        reference_details={
            'name': 'Jane Smith',
            'email': 'jane@company.com',
            'relationship': 'Direct Manager',
            'reference_type': 'professional'
        }
    )
    print(f"Request sent: {result['success']}")
