"""
Virtual Career Fair Service
3D virtual career fair platform with:
- Virtual booth spaces (Three.js/WebGL ready)
- Live video integration (Twilio Video)
- Real-time attendee tracking
- Digital swag bags and downloads
- Booth analytics for employers
- Networking features
- Chat and Q&A
- Event scheduling
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from extensions import db
from models import User, Company, Event, EventAttendee
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class VirtualCareerFairService:
    """
    Service for managing virtual career fairs with 3D environments
    """
    
    # Booth sizes and pricing
    BOOTH_TIERS = {
        'basic': {
            'name': 'Basic Booth',
            'price': 1000,
            'max_representatives': 2,
            'video_slots': 1,
            'features': ['Company logo', 'Basic info display', '1 video chat'],
            '3d_size': 'small',
            'customization': 'limited'
        },
        'standard': {
            'name': 'Standard Booth',
            'price': 2500,
            'max_representatives': 4,
            'video_slots': 2,
            'features': ['Company logo', 'Video banner', '2 video chats', 'Document downloads', 'Custom colors'],
            '3d_size': 'medium',
            'customization': 'moderate'
        },
        'premium': {
            'name': 'Premium Booth',
            'price': 5000,
            'max_representatives': 8,
            'video_slots': 4,
            'features': ['Custom 3D design', 'Video banner', '4 video chats', 'Document downloads', 'Live presentations', 'Analytics dashboard', 'Priority placement'],
            '3d_size': 'large',
            'customization': 'full'
        }
    }
    
    # Fair zones/halls
    FAIR_ZONES = [
        'Technology Hall', 'Healthcare & Science Hall', 'Business & Finance Hall',
        'Engineering Hall', 'Arts & Media Hall', 'Main Stage', 'Networking Lounge'
    ]
    
    @staticmethod
    def create_virtual_fair(
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        organizer_id: int,
        max_booths: int = 50,
        max_attendees: int = 1000,
        timezone: str = 'America/Chicago'
    ) -> Dict[str, Any]:
        """
        Create a new virtual career fair event
        
        Args:
            title: Fair title
            description: Fair description
            start_time: Start datetime
            end_time: End datetime
            organizer_id: University organizer user ID
            max_booths: Maximum number of booths
            max_attendees: Maximum attendees
            timezone: Event timezone
            
        Returns:
            Dictionary with fair details
        """
        try:
            organizer = User.query.get(organizer_id)
            if not organizer:
                return {'success': False, 'error': 'Organizer not found'}
            
            # Generate fair ID
            fair_id = hashlib.md5(f"{title}{start_time}".encode()).hexdigest()[:16]
            
            # Create fair data structure
            fair_data = {
                'fair_id': fair_id,
                'title': title,
                'description': description,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'timezone': timezone,
                'organizer_id': organizer_id,
                'max_booths': max_booths,
                'max_attendees': max_attendees,
                'status': 'planned',  # planned/active/completed
                'booth_count': 0,
                'registered_attendees': 0,
                'created_at': datetime.utcnow().isoformat(),
                'virtual_environment': {
                    'theme': 'modern_campus',
                    'zones': VirtualCareerFairService.FAIR_ZONES,
                    'spawn_point': {'x': 0, 'y': 0, 'z': 0},
                    'camera_mode': 'first_person'
                },
                'features': {
                    'live_chat': True,
                    'video_calls': True,
                    'presentations': True,
                    'networking_lounge': True,
                    'job_board': True,
                    'resume_drops': True
                }
            }
            
            # In production, save to VirtualFair model
            logger.info(f"Created virtual fair: {title} ({fair_id})")
            
            return {
                'success': True,
                'fair': fair_data,
                'admin_url': f'/admin/virtual-fairs/{fair_id}',
                'public_url': f'/virtual-fair/{fair_id}'
            }
            
        except Exception as e:
            logger.error(f"Error creating virtual fair: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_booth(
        fair_id: str,
        employer_id: int,
        company_id: int,
        booth_tier: str,
        zone: str,
        position: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Create a virtual booth for an employer
        
        Args:
            fair_id: Virtual fair ID
            employer_id: Employer user ID
            company_id: Company ID
            booth_tier: basic/standard/premium
            zone: Fair zone/hall
            position: 3D position coordinates {x, y, z}
            
        Returns:
            Dictionary with booth details
        """
        try:
            if booth_tier not in VirtualCareerFairService.BOOTH_TIERS:
                return {'success': False, 'error': 'Invalid booth tier'}
            
            employer = User.query.get(employer_id)
            company = Company.query.get(company_id)
            
            if not employer or not company:
                return {'success': False, 'error': 'Employer or company not found'}
            
            tier_info = VirtualCareerFairService.BOOTH_TIERS[booth_tier]
            booth_id = hashlib.md5(f"{fair_id}{company_id}".encode()).hexdigest()[:16]
            
            # Generate booth position if not provided
            if not position:
                position = VirtualCareerFairService._generate_booth_position(fair_id, zone)
            
            booth_data = {
                'booth_id': booth_id,
                'fair_id': fair_id,
                'employer_id': employer_id,
                'company_id': company_id,
                'company_name': company.name,
                'tier': booth_tier,
                'price': tier_info['price'],
                'zone': zone,
                'position': position,
                'status': 'pending_payment',  # pending_payment/active/inactive
                'created_at': datetime.utcnow().isoformat(),
                '3d_config': {
                    'size': tier_info['3d_size'],
                    'model': f'booth_{booth_tier}.glb',
                    'logo_texture': company.logo_url if hasattr(company, 'logo_url') else None,
                    'banner_video': None,
                    'custom_colors': {
                        'primary': '#1a56db',
                        'secondary': '#ffffff',
                        'accent': '#f59e0b'
                    },
                    'lighting': 'standard',
                    'animations': ['idle', 'attract_attention']
                },
                'features': tier_info['features'],
                'max_representatives': tier_info['max_representatives'],
                'video_slots': tier_info['video_slots'],
                'representatives': [],
                'materials': [],
                'analytics': {
                    'visits': 0,
                    'unique_visitors': 0,
                    'video_calls': 0,
                    'document_downloads': 0,
                    'resume_submissions': 0,
                    'avg_visit_duration_seconds': 0
                }
            }
            
            logger.info(f"Created {booth_tier} booth for {company.name} at fair {fair_id}")
            
            return {
                'success': True,
                'booth': booth_data,
                'payment_amount': tier_info['price'],
                'payment_url': f'/payment/booth/{booth_id}'
            }
            
        except Exception as e:
            logger.error(f"Error creating booth: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _generate_booth_position(fair_id: str, zone: str) -> Dict[str, float]:
        """
        Generate 3D position for booth in specified zone
        """
        # Zone-based positioning (simplified grid system)
        zone_positions = {
            'Technology Hall': {'x_start': 0, 'z_start': 0},
            'Healthcare & Science Hall': {'x_start': 50, 'z_start': 0},
            'Business & Finance Hall': {'x_start': 100, 'z_start': 0},
            'Engineering Hall': {'x_start': 0, 'z_start': 50},
            'Arts & Media Hall': {'x_start': 50, 'z_start': 50},
            'Main Stage': {'x_start': 75, 'z_start': 25},
            'Networking Lounge': {'x_start': 125, 'z_start': 25}
        }
        
        base = zone_positions.get(zone, {'x_start': 0, 'z_start': 0})
        
        # In production, query existing booths to find next available position
        # For now, return a base position
        return {
            'x': base['x_start'] + 10,
            'y': 0,
            'z': base['z_start'] + 10
        }
    
    @staticmethod
    def add_booth_representative(
        booth_id: str,
        user_id: int,
        role: str = 'recruiter'
    ) -> Dict[str, Any]:
        """
        Add a representative to a booth
        
        Args:
            booth_id: Booth ID
            user_id: User ID of representative
            role: recruiter/manager/specialist
            
        Returns:
            Dictionary with representative details
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            representative = {
                'user_id': user_id,
                'name': user.full_name,
                'role': role,
                'avatar_url': getattr(user, 'profile_image_url', None),
                'bio': getattr(user, 'bio', ''),
                'availability': 'available',  # available/busy/away
                'joined_at': datetime.utcnow().isoformat(),
                'video_room_id': None,
                'active_conversations': 0
            }
            
            logger.info(f"Added representative {user.full_name} to booth {booth_id}")
            
            return {
                'success': True,
                'representative': representative
            }
            
        except Exception as e:
            logger.error(f"Error adding representative: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def upload_booth_material(
        booth_id: str,
        material_type: str,
        file_url: str,
        title: str,
        description: str = None
    ) -> Dict[str, Any]:
        """
        Upload materials to booth (brochures, videos, job descriptions)
        
        Args:
            booth_id: Booth ID
            material_type: document/video/image/link
            file_url: URL to the file
            title: Material title
            description: Optional description
            
        Returns:
            Dictionary with material details
        """
        try:
            material_id = hashlib.md5(f"{booth_id}{file_url}{datetime.utcnow()}".encode()).hexdigest()[:16]
            
            material = {
                'material_id': material_id,
                'booth_id': booth_id,
                'type': material_type,
                'title': title,
                'description': description,
                'file_url': file_url,
                'download_count': 0,
                'uploaded_at': datetime.utcnow().isoformat(),
                'is_featured': False
            }
            
            logger.info(f"Uploaded {material_type} material to booth {booth_id}")
            
            return {
                'success': True,
                'material': material
            }
            
        except Exception as e:
            logger.error(f"Error uploading material: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def register_attendee(
        fair_id: str,
        user_id: int,
        interests: List[str] = None
    ) -> Dict[str, Any]:
        """
        Register user as attendee for virtual fair
        
        Args:
            fair_id: Virtual fair ID
            user_id: User ID
            interests: List of interest categories
            
        Returns:
            Dictionary with registration details
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            registration_id = hashlib.md5(f"{fair_id}{user_id}".encode()).hexdigest()[:16]
            
            registration = {
                'registration_id': registration_id,
                'fair_id': fair_id,
                'user_id': user_id,
                'user_name': user.full_name,
                'email': user.email,
                'interests': interests or [],
                'registered_at': datetime.utcnow().isoformat(),
                'checked_in': False,
                'check_in_time': None,
                'avatar_config': {
                    'model': 'default_student',
                    'skin_tone': 'default',
                    'hair_style': 'default',
                    'outfit': 'business_casual'
                },
                'swag_bag': [],  # Digital swag collected
                'booth_visits': [],
                'connections_made': 0,
                'resume_submitted': False
            }
            
            logger.info(f"Registered user {user_id} for fair {fair_id}")
            
            return {
                'success': True,
                'registration': registration,
                'access_url': f'/virtual-fair/{fair_id}/enter',
                'calendar_invite': True
            }
            
        except Exception as e:
            logger.error(f"Error registering attendee: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def track_booth_visit(
        booth_id: str,
        user_id: int,
        duration_seconds: int = None
    ) -> Dict[str, Any]:
        """
        Track when a user visits a booth
        
        Args:
            booth_id: Booth ID
            user_id: Visitor user ID
            duration_seconds: How long they stayed
            
        Returns:
            Dictionary with visit tracking
        """
        try:
            visit_id = hashlib.md5(f"{booth_id}{user_id}{datetime.utcnow()}".encode()).hexdigest()[:16]
            
            visit = {
                'visit_id': visit_id,
                'booth_id': booth_id,
                'user_id': user_id,
                'visited_at': datetime.utcnow().isoformat(),
                'duration_seconds': duration_seconds,
                'actions': {
                    'viewed_materials': False,
                    'downloaded_materials': False,
                    'started_video_call': False,
                    'submitted_resume': False,
                    'asked_question': False
                }
            }
            
            # In production, update booth analytics
            logger.info(f"Tracked visit to booth {booth_id} by user {user_id}")
            
            return {
                'success': True,
                'visit': visit
            }
            
        except Exception as e:
            logger.error(f"Error tracking booth visit: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def start_booth_video_call(
        booth_id: str,
        attendee_id: int,
        representative_id: int
    ) -> Dict[str, Any]:
        """
        Start a video call between attendee and booth representative
        Uses Twilio Video (integrates with video_interview_service)
        
        Args:
            booth_id: Booth ID
            attendee_id: Attendee user ID
            representative_id: Representative user ID
            
        Returns:
            Dictionary with video call details
        """
        try:
            attendee = User.query.get(attendee_id)
            representative = User.query.get(representative_id)
            
            if not attendee or not representative:
                return {'success': False, 'error': 'User not found'}
            
            # Generate video room (would integrate with Twilio Video)
            room_id = hashlib.md5(f"{booth_id}{attendee_id}{representative_id}".encode()).hexdigest()[:16]
            room_name = f"booth_{booth_id}_{room_id}"
            
            call_data = {
                'call_id': room_id,
                'booth_id': booth_id,
                'room_name': room_name,
                'attendee_id': attendee_id,
                'representative_id': representative_id,
                'started_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'duration_seconds': 0,
                'twilio_room_sid': None,  # Would be populated by Twilio
                'recording_enabled': False
            }
            
            # In production, integrate with video_interview_service
            # from services.video_interview_service import VideoInterviewService
            # twilio_room = VideoInterviewService.create_interview_room(...)
            
            logger.info(f"Started video call at booth {booth_id}")
            
            return {
                'success': True,
                'call': call_data,
                'join_url_attendee': f'/virtual-fair/video/{room_id}/attendee',
                'join_url_representative': f'/virtual-fair/video/{room_id}/representative',
                'access_token_attendee': 'twilio_token_here',
                'access_token_representative': 'twilio_token_here'
            }
            
        except Exception as e:
            logger.error(f"Error starting video call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_to_swag_bag(
        registration_id: str,
        item_type: str,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add digital swag to attendee's bag
        
        Args:
            registration_id: Registration ID
            item_type: coupon/ebook/trial/merchandise
            item_data: Item details
            
        Returns:
            Dictionary with swag item
        """
        try:
            swag_item = {
                'item_id': hashlib.md5(f"{registration_id}{item_type}{datetime.utcnow()}".encode()).hexdigest()[:16],
                'registration_id': registration_id,
                'type': item_type,
                'data': item_data,
                'collected_at': datetime.utcnow().isoformat(),
                'redeemed': False,
                'redemption_code': hashlib.md5(f"code{registration_id}".encode()).hexdigest()[:8].upper()
            }
            
            logger.info(f"Added {item_type} to swag bag for registration {registration_id}")
            
            return {
                'success': True,
                'swag_item': swag_item
            }
            
        except Exception as e:
            logger.error(f"Error adding to swag bag: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_booth_analytics(booth_id: str, employer_id: int) -> Dict[str, Any]:
        """
        Get detailed analytics for a booth
        
        Args:
            booth_id: Booth ID
            employer_id: Employer ID (for authorization)
            
        Returns:
            Dictionary with booth analytics
        """
        try:
            # In production, aggregate from database
            analytics = {
                'booth_id': booth_id,
                'total_visits': 147,
                'unique_visitors': 112,
                'avg_visit_duration_seconds': 245,
                'peak_traffic_hour': '14:00-15:00',
                'video_calls': {
                    'total': 23,
                    'completed': 21,
                    'avg_duration_minutes': 12.5
                },
                'materials': {
                    'total_downloads': 87,
                    'most_popular': 'Company_Overview.pdf (34 downloads)'
                },
                'resume_submissions': 34,
                'visitor_demographics': {
                    'majors': {
                        'Computer Science': 42,
                        'Business': 28,
                        'Engineering': 22,
                        'Other': 20
                    },
                    'graduation_years': {
                        '2025': 45,
                        '2026': 38,
                        '2027': 29
                    }
                },
                'engagement_funnel': {
                    'visited': 147,
                    'viewed_materials': 95,
                    'downloaded_materials': 87,
                    'started_video_call': 23,
                    'submitted_resume': 34
                },
                'conversion_rate': 23.1,  # (resumed / visited) * 100
                'top_questions': [
                    'What positions are available?',
                    'What is the salary range?',
                    'Do you sponsor visas?'
                ],
                'visitor_feedback_score': 4.6,  # Out of 5
                'recommendation_score': 8.5  # NPS style, out of 10
            }
            
            logger.info(f"Retrieved analytics for booth {booth_id}")
            
            return {
                'success': True,
                'analytics': analytics,
                'export_url': f'/api/booth/{booth_id}/analytics/export'
            }
            
        except Exception as e:
            logger.error(f"Error getting booth analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_fair_overview(fair_id: str) -> Dict[str, Any]:
        """
        Get overview statistics for entire fair
        
        Args:
            fair_id: Virtual fair ID
            
        Returns:
            Dictionary with fair statistics
        """
        try:
            # In production, aggregate from database
            overview = {
                'fair_id': fair_id,
                'status': 'active',
                'total_booths': 42,
                'total_registered': 847,
                'total_checked_in': 623,
                'currently_online': 284,
                'peak_concurrent_users': 412,
                'total_video_calls': 189,
                'total_resume_submissions': 523,
                'total_material_downloads': 1847,
                'booth_distribution': {
                    'Technology Hall': 15,
                    'Healthcare & Science Hall': 8,
                    'Business & Finance Hall': 10,
                    'Engineering Hall': 6,
                    'Arts & Media Hall': 3
                },
                'attendee_activity': {
                    'avg_booths_visited': 3.7,
                    'avg_session_duration_minutes': 42,
                    'avg_materials_downloaded': 2.2
                },
                'popular_booths': [
                    {'company': 'Google', 'visits': 234},
                    {'company': 'Microsoft', 'visits': 198},
                    {'company': 'Amazon', 'visits': 176}
                ],
                'engagement_metrics': {
                    'chat_messages': 2847,
                    'video_calls_initiated': 189,
                    'connections_made': 445,
                    'job_applications': 156
                },
                'revenue': {
                    'booth_sales': 78500,
                    'premium_upgrades': 12000,
                    'sponsorships': 25000,
                    'total': 115500
                }
            }
            
            logger.info(f"Retrieved overview for fair {fair_id}")
            
            return {
                'success': True,
                'overview': overview,
                'real_time_dashboard_url': f'/admin/fair/{fair_id}/dashboard'
            }
            
        except Exception as e:
            logger.error(f"Error getting fair overview: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_networking_suggestions(user_id: int, fair_id: str) -> Dict[str, Any]:
        """
        Suggest people to network with based on interests and goals
        
        Args:
            user_id: User ID
            fair_id: Virtual fair ID
            
        Returns:
            Dictionary with networking suggestions
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # In production, use ML to match based on interests, majors, goals
            suggestions = []
            
            # Suggest other students
            suggestions.append({
                'type': 'student',
                'user_id': 'student_123',
                'name': 'Alice Johnson',
                'major': getattr(user, 'major', 'Computer Science'),
                'graduation_year': 2025,
                'interests': ['Software Engineering', 'AI', 'Startups'],
                'match_score': 92,
                'reason': 'Same major and career interests',
                'currently_at_booth': 'Google',
                'available_for_chat': True
            })
            
            # Suggest alumni
            suggestions.append({
                'type': 'alumni',
                'user_id': 'alumni_456',
                'name': 'Bob Smith',
                'current_title': 'Senior Engineer at Microsoft',
                'graduation_year': 2020,
                'major': getattr(user, 'major', 'Computer Science'),
                'match_score': 88,
                'reason': 'Alumni from your major, works at target company',
                'willing_to_mentor': True,
                'available_for_chat': True
            })
            
            # Suggest recruiters
            suggestions.append({
                'type': 'recruiter',
                'user_id': 'recruiter_789',
                'name': 'Carol Davis',
                'company': 'Amazon',
                'title': 'Technical Recruiter',
                'booth_id': 'booth_amazon',
                'match_score': 85,
                'reason': 'Hiring for positions matching your skills',
                'available_now': True
            })
            
            logger.info(f"Generated networking suggestions for user {user_id}")
            
            return {
                'success': True,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error getting networking suggestions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_presentation_session(
        booth_id: str,
        title: str,
        presenter_id: int,
        start_time: datetime,
        duration_minutes: int = 30,
        max_attendees: int = 100
    ) -> Dict[str, Any]:
        """
        Create a live presentation session at a booth
        
        Args:
            booth_id: Booth ID
            title: Presentation title
            presenter_id: Presenter user ID
            start_time: Start time
            duration_minutes: Duration
            max_attendees: Max attendees
            
        Returns:
            Dictionary with session details
        """
        try:
            presenter = User.query.get(presenter_id)
            if not presenter:
                return {'success': False, 'error': 'Presenter not found'}
            
            session_id = hashlib.md5(f"{booth_id}{title}{start_time}".encode()).hexdigest()[:16]
            
            session = {
                'session_id': session_id,
                'booth_id': booth_id,
                'title': title,
                'presenter_id': presenter_id,
                'presenter_name': presenter.full_name,
                'start_time': start_time.isoformat(),
                'duration_minutes': duration_minutes,
                'end_time': (start_time + timedelta(minutes=duration_minutes)).isoformat(),
                'max_attendees': max_attendees,
                'registered_attendees': 0,
                'status': 'scheduled',  # scheduled/live/completed/cancelled
                'stream_url': f'/virtual-fair/stream/{session_id}',
                'chat_enabled': True,
                'q_and_a_enabled': True,
                'recording_enabled': True
            }
            
            logger.info(f"Created presentation session: {title} at booth {booth_id}")
            
            return {
                'success': True,
                'session': session,
                'registration_url': f'/virtual-fair/sessions/{session_id}/register'
            }
            
        except Exception as e:
            logger.error(f"Error creating presentation session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_3d_scene_data(fair_id: str) -> Dict[str, Any]:
        """
        Get 3D scene data for Three.js rendering
        
        Args:
            fair_id: Virtual fair ID
            
        Returns:
            Dictionary with 3D scene configuration
        """
        try:
            # Scene configuration for Three.js
            scene_data = {
                'fair_id': fair_id,
                'environment': {
                    'skybox': 'campus_sky.hdr',
                    'ground': 'grass_texture.jpg',
                    'ambient_light': {
                        'color': '#ffffff',
                        'intensity': 0.5
                    },
                    'directional_light': {
                        'color': '#ffffff',
                        'intensity': 1.0,
                        'position': [100, 100, 50],
                        'cast_shadow': True
                    },
                    'fog': {
                        'enabled': True,
                        'color': '#87CEEB',
                        'near': 200,
                        'far': 1000
                    }
                },
                'camera': {
                    'type': 'PerspectiveCamera',
                    'fov': 75,
                    'near': 0.1,
                    'far': 2000,
                    'initial_position': [0, 5, 20],
                    'initial_target': [0, 0, 0]
                },
                'booths': [
                    {
                        'booth_id': 'booth_001',
                        'company': 'Google',
                        'position': [10, 0, 10],
                        'rotation': [0, 0, 0],
                        'model': 'booth_premium.glb',
                        'scale': [1, 1, 1],
                        'collider': 'box',
                        'interactive': True,
                        'logo_texture': 'google_logo.png',
                        'banner_video': 'google_intro.mp4'
                    },
                    {
                        'booth_id': 'booth_002',
                        'company': 'Microsoft',
                        'position': [30, 0, 10],
                        'rotation': [0, 0, 0],
                        'model': 'booth_standard.glb',
                        'scale': [1, 1, 1],
                        'collider': 'box',
                        'interactive': True,
                        'logo_texture': 'microsoft_logo.png'
                    }
                ],
                'navigation': {
                    'waypoints': [
                        {'id': 'entrance', 'position': [0, 0, 0], 'label': 'Entrance'},
                        {'id': 'tech_hall', 'position': [25, 0, 10], 'label': 'Technology Hall'},
                        {'id': 'main_stage', 'position': [75, 0, 25], 'label': 'Main Stage'}
                    ],
                    'teleport_zones': [
                        {'from': 'entrance', 'to': 'tech_hall'},
                        {'from': 'entrance', 'to': 'main_stage'}
                    ]
                },
                'ui_elements': [
                    {
                        'type': 'minimap',
                        'position': 'bottom-right',
                        'size': [200, 200],
                        'zoom_level': 1
                    },
                    {
                        'type': 'attendee_counter',
                        'position': 'top-right',
                        'show_avatars': True
                    }
                ],
                'physics': {
                    'gravity': -9.8,
                    'collision_detection': True,
                    'player_height': 1.8,
                    'player_radius': 0.5
                },
                'audio': {
                    'ambient_music': 'fair_background.mp3',
                    'volume': 0.3,
                    'spatial_audio': True
                }
            }
            
            logger.info(f"Retrieved 3D scene data for fair {fair_id}")
            
            return {
                'success': True,
                'scene': scene_data,
                'assets_cdn': 'https://cdn.pittstate.edu/virtual-fair-assets/'
            }
            
        except Exception as e:
            logger.error(f"Error getting 3D scene data: {str(e)}")
            return {'success': False, 'error': str(e)}
