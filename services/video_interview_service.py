"""
Video Interview Service for PittState Connect
Implements Twilio Video API for employer-candidate interviews
Includes room management, recording, and analytics
"""

from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from extensions import db
from models import User
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Twilio Video client
try:
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_API_KEY = os.getenv('TWILIO_API_KEY_SID')
    TWILIO_API_SECRET = os.getenv('TWILIO_API_KEY_SECRET')
    
    if TWILIO_ACCOUNT_SID and TWILIO_API_KEY:
        twilio_client = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
        logger.info("✅ Twilio Video client initialized")
    else:
        twilio_client = None
        logger.warning("⚠️ Twilio Video credentials not configured")
except Exception as e:
    twilio_client = None
    logger.error(f"❌ Twilio Video initialization failed: {str(e)}")


class VideoInterviewService:
    """Service for managing video interviews"""
    
    @staticmethod
    def create_interview_room(interview_id, employer_user_id, candidate_user_id, scheduled_time, duration_minutes=60):
        """
        Create a new video interview room
        
        Args:
            interview_id: Unique interview ID
            employer_user_id: User ID of employer
            candidate_user_id: User ID of candidate
            scheduled_time: Datetime of scheduled interview
            duration_minutes: Interview duration in minutes
            
        Returns:
            dict: Room details or None if failed
        """
        if not twilio_client:
            logger.error("Twilio Video client not initialized")
            return None
        
        try:
            from models_extended import VideoInterview
            
            # Create unique room name
            room_name = f"interview_{interview_id}_{int(datetime.now().timestamp())}"
            
            # Create Twilio video room
            room = twilio_client.video.rooms.create(
                unique_name=room_name,
                type='group',  # Supports up to 50 participants
                max_participants=5,  # Employer, candidate, + optional observers
                record_participants_on_connect=True,  # Auto-record
                status_callback=os.getenv('TWILIO_VIDEO_CALLBACK_URL'),
                status_callback_method='POST'
            )
            
            # Save to database
            video_interview = VideoInterview(
                interview_id=interview_id,
                room_sid=room.sid,
                room_name=room_name,
                employer_user_id=employer_user_id,
                candidate_user_id=candidate_user_id,
                scheduled_time=scheduled_time,
                duration_minutes=duration_minutes,
                status='scheduled',
                created_at=datetime.now()
            )
            
            db.session.add(video_interview)
            db.session.commit()
            
            logger.info(f"✅ Created video interview room: {room_name}")
            
            return {
                'room_sid': room.sid,
                'room_name': room_name,
                'interview_id': interview_id,
                'scheduled_time': scheduled_time.isoformat(),
                'duration_minutes': duration_minutes,
                'status': 'scheduled'
            }
            
        except Exception as e:
            logger.error(f"Error creating interview room: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def generate_access_token(room_name, user_id, duration_hours=2):
        """
        Generate access token for user to join video room
        
        Args:
            room_name: Video room name
            user_id: User ID
            duration_hours: Token validity duration
            
        Returns:
            str: JWT access token
        """
        if not TWILIO_ACCOUNT_SID or not TWILIO_API_KEY:
            logger.error("Twilio credentials not configured")
            return None
        
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
            
            # Create access token
            token = AccessToken(
                TWILIO_ACCOUNT_SID,
                TWILIO_API_KEY,
                TWILIO_API_SECRET,
                identity=f"{user.id}_{user.full_name}",
                ttl=duration_hours * 3600
            )
            
            # Add video grant
            video_grant = VideoGrant(room=room_name)
            token.add_grant(video_grant)
            
            jwt_token = token.to_jwt()
            
            logger.info(f"✅ Generated access token for user {user_id} in room {room_name}")
            
            return jwt_token.decode('utf-8') if isinstance(jwt_token, bytes) else jwt_token
            
        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            return None
    
    @staticmethod
    def start_interview(interview_id, user_id):
        """
        Start an interview (user joins room)
        
        Args:
            interview_id: Interview ID
            user_id: User joining
            
        Returns:
            dict: Join details with access token
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview:
                logger.error(f"Interview not found: {interview_id}")
                return None
            
            # Verify user is authorized (employer or candidate)
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                logger.error(f"User {user_id} not authorized for interview {interview_id}")
                return None
            
            # Generate access token
            access_token = VideoInterviewService.generate_access_token(
                interview.room_name,
                user_id,
                duration_hours=interview.duration_minutes // 60 + 1
            )
            
            if not access_token:
                return None
            
            # Update interview status
            if interview.status == 'scheduled':
                interview.status = 'in_progress'
                interview.started_at = datetime.now()
            
            # Track participant join
            if user_id == interview.employer_user_id and not interview.employer_joined_at:
                interview.employer_joined_at = datetime.now()
            elif user_id == interview.candidate_user_id and not interview.candidate_joined_at:
                interview.candidate_joined_at = datetime.now()
            
            db.session.commit()
            
            return {
                'room_name': interview.room_name,
                'access_token': access_token,
                'interview_id': interview_id,
                'status': interview.status,
                'duration_minutes': interview.duration_minutes
            }
            
        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def end_interview(interview_id, user_id):
        """
        End an interview
        
        Args:
            interview_id: Interview ID
            user_id: User ending (must be employer or candidate)
            
        Returns:
            bool: Success status
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview:
                return False
            
            # Verify authorization
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                return False
            
            # Complete room on Twilio
            if twilio_client and interview.room_sid:
                try:
                    twilio_client.video.rooms(interview.room_sid).update(status='completed')
                except Exception as e:
                    logger.warning(f"Failed to complete Twilio room: {str(e)}")
            
            # Update interview
            interview.status = 'completed'
            interview.ended_at = datetime.now()
            
            # Calculate actual duration
            if interview.started_at:
                duration = (interview.ended_at - interview.started_at).total_seconds() / 60
                interview.actual_duration_minutes = int(duration)
            
            db.session.commit()
            
            logger.info(f"✅ Interview {interview_id} ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending interview: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_interview_details(interview_id, user_id):
        """
        Get interview details for authorized user
        
        Args:
            interview_id: Interview ID
            user_id: Requesting user ID
            
        Returns:
            dict: Interview details
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview:
                return None
            
            # Verify authorization
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                logger.warning(f"User {user_id} not authorized for interview {interview_id}")
                return None
            
            employer = User.query.get(interview.employer_user_id)
            candidate = User.query.get(interview.candidate_user_id)
            
            return {
                'interview_id': interview.interview_id,
                'room_name': interview.room_name,
                'employer': {
                    'id': employer.id,
                    'name': employer.full_name,
                    'email': employer.email
                } if employer else None,
                'candidate': {
                    'id': candidate.id,
                    'name': candidate.full_name,
                    'email': candidate.email
                } if candidate else None,
                'scheduled_time': interview.scheduled_time.isoformat() if interview.scheduled_time else None,
                'duration_minutes': interview.duration_minutes,
                'status': interview.status,
                'started_at': interview.started_at.isoformat() if interview.started_at else None,
                'ended_at': interview.ended_at.isoformat() if interview.ended_at else None,
                'recording_url': interview.recording_url,
                'recording_duration': interview.recording_duration_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting interview details: {str(e)}")
            return None
    
    @staticmethod
    def get_recordings(interview_id, user_id):
        """
        Get interview recordings
        
        Args:
            interview_id: Interview ID
            user_id: Requesting user ID
            
        Returns:
            list: Recording URLs and metadata
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview or not interview.room_sid:
                return []
            
            # Verify authorization
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                return []
            
            if not twilio_client:
                return []
            
            # Fetch recordings from Twilio
            recordings = twilio_client.video.recordings.list(room_sid=interview.room_sid)
            
            recording_list = []
            for recording in recordings:
                recording_list.append({
                    'sid': recording.sid,
                    'status': recording.status,
                    'date_created': recording.date_created.isoformat() if recording.date_created else None,
                    'duration': recording.duration,
                    'size': recording.size,
                    'url': f"https://video.twilio.com/v1/Recordings/{recording.sid}/Media",
                    'type': recording.type
                })
            
            # Update database with recording info
            if recording_list and not interview.recording_url:
                interview.recording_url = recording_list[0]['url']
                interview.recording_duration_seconds = recording_list[0]['duration']
                db.session.commit()
            
            return recording_list
            
        except Exception as e:
            logger.error(f"Error fetching recordings: {str(e)}")
            return []
    
    @staticmethod
    def get_user_interviews(user_id, status=None, upcoming_only=False):
        """
        Get all interviews for a user
        
        Args:
            user_id: User ID
            status: Filter by status (scheduled, in_progress, completed, cancelled)
            upcoming_only: Only return future interviews
            
        Returns:
            list: Interview details
        """
        try:
            from models_extended import VideoInterview
            
            query = VideoInterview.query.filter(
                (VideoInterview.employer_user_id == user_id) | 
                (VideoInterview.candidate_user_id == user_id)
            )
            
            if status:
                query = query.filter_by(status=status)
            
            if upcoming_only:
                query = query.filter(VideoInterview.scheduled_time >= datetime.now())
            
            interviews = query.order_by(VideoInterview.scheduled_time.desc()).all()
            
            result = []
            for interview in interviews:
                employer = User.query.get(interview.employer_user_id)
                candidate = User.query.get(interview.candidate_user_id)
                
                result.append({
                    'interview_id': interview.interview_id,
                    'employer_name': employer.full_name if employer else None,
                    'candidate_name': candidate.full_name if candidate else None,
                    'scheduled_time': interview.scheduled_time.isoformat() if interview.scheduled_time else None,
                    'duration_minutes': interview.duration_minutes,
                    'status': interview.status,
                    'has_recording': bool(interview.recording_url)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user interviews: {str(e)}")
            return []
    
    @staticmethod
    def cancel_interview(interview_id, user_id, reason=None):
        """
        Cancel a scheduled interview
        
        Args:
            interview_id: Interview ID
            user_id: User cancelling
            reason: Cancellation reason
            
        Returns:
            bool: Success status
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview:
                return False
            
            # Verify authorization
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                return False
            
            # Can only cancel scheduled interviews
            if interview.status != 'scheduled':
                return False
            
            interview.status = 'cancelled'
            interview.cancelled_by_user_id = user_id
            interview.cancellation_reason = reason
            interview.cancelled_at = datetime.now()
            
            db.session.commit()
            
            # Send notification to other party
            other_user_id = interview.candidate_user_id if user_id == interview.employer_user_id else interview.employer_user_id
            VideoInterviewService._notify_cancellation(interview_id, other_user_id, reason)
            
            logger.info(f"✅ Interview {interview_id} cancelled by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling interview: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _notify_cancellation(interview_id, user_id, reason):
        """Send cancellation notification"""
        try:
            from services.communication_service import CommunicationService
            
            user = User.query.get(user_id)
            if user:
                message = f"Your interview (ID: {interview_id}) has been cancelled."
                if reason:
                    message += f" Reason: {reason}"
                
                CommunicationService.send_notification(
                    user_id=user_id,
                    notification_type='interview_cancelled',
                    title='Interview Cancelled',
                    message=message,
                    action_url=f"/interviews/{interview_id}"
                )
        except Exception as e:
            logger.error(f"Error sending cancellation notification: {str(e)}")
    
    @staticmethod
    def reschedule_interview(interview_id, user_id, new_scheduled_time):
        """
        Reschedule an interview
        
        Args:
            interview_id: Interview ID
            user_id: User requesting reschedule
            new_scheduled_time: New datetime
            
        Returns:
            bool: Success status
        """
        try:
            from models_extended import VideoInterview
            
            interview = VideoInterview.query.filter_by(interview_id=interview_id).first()
            if not interview:
                return False
            
            # Verify authorization
            if user_id not in [interview.employer_user_id, interview.candidate_user_id]:
                return False
            
            # Can only reschedule scheduled interviews
            if interview.status != 'scheduled':
                return False
            
            old_time = interview.scheduled_time
            interview.scheduled_time = new_scheduled_time
            interview.rescheduled_count = (interview.rescheduled_count or 0) + 1
            
            db.session.commit()
            
            # Notify other party
            other_user_id = interview.candidate_user_id if user_id == interview.employer_user_id else interview.employer_user_id
            VideoInterviewService._notify_reschedule(interview_id, other_user_id, old_time, new_scheduled_time)
            
            logger.info(f"✅ Interview {interview_id} rescheduled to {new_scheduled_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error rescheduling interview: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _notify_reschedule(interview_id, user_id, old_time, new_time):
        """Send reschedule notification"""
        try:
            from services.communication_service import CommunicationService
            
            user = User.query.get(user_id)
            if user:
                message = f"Your interview has been rescheduled from {old_time.strftime('%Y-%m-%d %H:%M')} to {new_time.strftime('%Y-%m-%d %H:%M')}."
                
                CommunicationService.send_notification(
                    user_id=user_id,
                    notification_type='interview_rescheduled',
                    title='Interview Rescheduled',
                    message=message,
                    action_url=f"/interviews/{interview_id}"
                )
        except Exception as e:
            logger.error(f"Error sending reschedule notification: {str(e)}")
