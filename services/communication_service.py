"""
Communication Service
Unified inbox, notifications, email, calendar sync, messaging, SMS, WhatsApp
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from extensions import db, mail
from models_extended import Message, Announcement, CalendarSync, Forum, ForumThread, Webinar, WebinarRegistration
from models_growth_features import ForumPost
from models import Notification, User
from flask_mail import Message as MailMessage
import logging
import os

logger = logging.getLogger(__name__)

# Twilio setup for SMS/WhatsApp
try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
    
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None
except ImportError:
    twilio_client = None
    logger.warning("Twilio not installed. SMS/WhatsApp features disabled.")


class CommunicationService:
    """Unified communication system"""
    
    def __init__(self):
        """Initialize communication service with dependencies"""
        self.logger = logger
        self.twilio_client = twilio_client
        self.mail_enabled = mail is not None
        
        # SMS/WhatsApp configuration
        self.sms_enabled = twilio_client is not None and TWILIO_PHONE_NUMBER
        self.whatsapp_enabled = twilio_client is not None and TWILIO_WHATSAPP_NUMBER
        
        # Rate limiting configuration
        self.max_sms_per_hour = 50
        self.max_emails_per_hour = 100
        self.max_notifications_per_hour = 200
        
        # Feature flags
        self.features = {
            'unified_inbox': True,
            'email_notifications': self.mail_enabled,
            'sms_notifications': self.sms_enabled,
            'whatsapp_notifications': self.whatsapp_enabled,
            'calendar_sync': True,
            'forums': True,
            'webinars': True
        }
        
        self.logger.info(f"Communication Service initialized with features: {self.features}")
    
    # ============================================================
    # UNIFIED INBOX
    # ============================================================
    
    def get_unified_inbox(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Get unified inbox combining messages, notifications, and announcements
        """
        try:
            # Get messages
            messages = Message.query.filter_by(recipient_id=user_id).order_by(
                Message.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            # Get notifications
            notifications = Notification.query.filter_by(recipient_id=user_id).order_by(
                Notification.timestamp.desc()
            ).limit(20).all()
            
            # Get relevant announcements
            announcements = Announcement.query.filter(
                Announcement.published_at <= datetime.utcnow(),
                or_(
                    Announcement.expires_at == None,
                    Announcement.expires_at >= datetime.utcnow()
                )
            ).order_by(Announcement.published_at.desc()).limit(10).all()
            
            return {
                "messages": {
                    "items": [self._serialize_message(m) for m in messages.items],
                    "total": messages.total,
                    "pages": messages.pages,
                    "current_page": page
                },
                "notifications": [self._serialize_notification(n) for n in notifications],
                "announcements": [self._serialize_announcement(a) for a in announcements],
                "unread_count": self._count_unread(user_id)
            }
            
        except Exception as e:
            logger.error(f"Unified inbox error: {e}")
            return {"error": str(e)}
    
    def _count_unread(self, user_id: int) -> Dict[str, int]:
        """Count unread items"""
        return {
            "messages": Message.query.filter_by(recipient_id=user_id, is_read=False).count(),
            "notifications": Notification.query.filter_by(recipient_id=user_id, is_read=False).count()
        }
    
    # ============================================================
    # MESSAGING
    # ============================================================
    
    def send_message(
        self,
        sender_id: int,
        recipient_id: int,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        encrypted: bool = False
    ) -> Dict[str, Any]:
        """
        Send internal message
        """
        try:
            import uuid
            
            if not thread_id:
                thread_id = str(uuid.uuid4())
            
            message = Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                subject=subject,
                body=body,
                thread_id=thread_id,
                attachments=attachments,
                encrypted=encrypted
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Create notification
            self.create_notification(
                recipient_id=recipient_id,
                message=f"New message from {message.sender.full_name}: {subject}",
                category="message",
                link=f"/messages/{message.id}"
            )
            
            return {
                "success": True,
                "message_id": message.id,
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def mark_message_read(self, message_id: int, user_id: int) -> bool:
        """Mark message as read"""
        try:
            message = Message.query.filter_by(id=message_id, recipient_id=user_id).first()
            if message:
                message.is_read = True
                message.read_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Mark message read error: {e}")
            return False
    
    def get_conversation_thread(self, thread_id: str, user_id: int) -> List[Message]:
        """Get all messages in a thread"""
        return Message.query.filter(
            Message.thread_id == thread_id,
            or_(
                Message.sender_id == user_id,
                Message.recipient_id == user_id
            )
        ).order_by(Message.created_at.asc()).all()
    
    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    
    def create_notification(
        self,
        recipient_id: int,
        message: str,
        category: str = "info",
        link: Optional[str] = None
    ) -> bool:
        """
        Create system notification
        """
        try:
            notification = Notification(
                recipient_id=recipient_id,
                message=message,
                category=category,
                link=link
            )
            db.session.add(notification)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Create notification error: {e}")
            db.session.rollback()
            return False
    
    def bulk_notify(self, user_ids: List[int], message: str, category: str = "info", link: Optional[str] = None) -> int:
        """Send notification to multiple users"""
        count = 0
        for user_id in user_ids:
            if self.create_notification(user_id, message, category, link):
                count += 1
        return count
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = Notification.query.filter_by(id=notification_id, recipient_id=user_id).first()
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Mark notification read error: {e}")
            return False
    
    # ============================================================
    # EMAIL
    # ============================================================
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        attachments: Optional[List] = None
    ) -> bool:
        """
        Send email via Flask-Mail
        """
        try:
            msg = MailMessage(
                subject=subject,
                recipients=[to],
                body=body,
                html=html
            )
            
            if attachments:
                for attachment in attachments:
                    msg.attach(
                        attachment.get("filename"),
                        attachment.get("content_type"),
                        attachment.get("data")
                    )
            
            mail.send(msg)
            logger.info(f"Email sent to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    def send_bulk_email(self, recipients: List[str], subject: str, body: str, html: Optional[str] = None) -> int:
        """Send email to multiple recipients"""
        count = 0
        for recipient in recipients:
            if self.send_email(recipient, subject, body, html):
                count += 1
        return count
    
    # ============================================================
    # ANNOUNCEMENTS
    # ============================================================
    
    def create_announcement(
        self,
        title: str,
        content: str,
        author_id: int,
        department_id: Optional[int] = None,
        priority: str = "normal",
        target_audience: List[str] = None,
        publish_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create system/department announcement
        """
        try:
            announcement = Announcement(
                title=title,
                content=content,
                author_id=author_id,
                department_id=department_id,
                priority=priority,
                target_audience=target_audience or ["all"],
                published_at=publish_at or datetime.utcnow(),
                expires_at=expires_at
            )
            
            db.session.add(announcement)
            db.session.commit()
            
            # Notify relevant users
            if "all" in (target_audience or []):
                users = User.query.limit(100).all()  # Batch notify
                for user in users:
                    self.create_notification(
                        user.id,
                        f"New announcement: {title}",
                        "announcement",
                        f"/announcements/{announcement.id}"
                    )
            
            return {
                "success": True,
                "announcement_id": announcement.id
            }
            
        except Exception as e:
            logger.error(f"Create announcement error: {e}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def get_active_announcements(self, department_id: Optional[int] = None, limit: int = 10) -> List[Announcement]:
        """Get active announcements"""
        query = Announcement.query.filter(
            Announcement.published_at <= datetime.utcnow(),
            or_(
                Announcement.expires_at == None,
                Announcement.expires_at >= datetime.utcnow()
            )
        )
        
        if department_id:
            query = query.filter(
                or_(
                    Announcement.department_id == department_id,
                    Announcement.department_id == None
                )
            )
        
        return query.order_by(Announcement.priority.desc(), Announcement.published_at.desc()).limit(limit).all()
    
    # ============================================================
    # FORUMS
    # ============================================================
    
    def create_forum(self, name: str, description: str, category: str, creator_id: int, is_private: bool = False) -> int:
        """Create discussion forum"""
        try:
            forum = Forum(
                name=name,
                description=description,
                category=category,
                created_by=creator_id,
                is_private=is_private
            )
            db.session.add(forum)
            db.session.commit()
            return forum.id
        except Exception as e:
            logger.error(f"Create forum error: {e}")
            db.session.rollback()
            return 0
    
    def create_forum_thread(
        self,
        forum_id: int,
        title: str,
        content: str,
        author_id: int
    ) -> int:
        """Create forum discussion thread"""
        try:
            thread = ForumThread(
                forum_id=forum_id,
                title=title,
                content=content,
                author_id=author_id
            )
            db.session.add(thread)
            db.session.commit()
            return thread.id
        except Exception as e:
            logger.error(f"Create forum thread error: {e}")
            db.session.rollback()
            return 0
    
    def post_forum_reply(
        self,
        thread_id: int,
        content: str,
        author_id: int,
        parent_post_id: Optional[int] = None
    ) -> int:
        """Post reply to forum thread"""
        try:
            post = ForumPost(
                thread_id=thread_id,
                content=content,
                author_id=author_id,
                parent_post_id=parent_post_id
            )
            db.session.add(post)
            db.session.commit()
            return post.id
        except Exception as e:
            logger.error(f"Post forum reply error: {e}")
            db.session.rollback()
            return 0
    
    def get_forum_threads(self, forum_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """Get forum threads with pagination"""
        threads = ForumThread.query.filter_by(forum_id=forum_id).order_by(
            ForumThread.is_pinned.desc(),
            ForumThread.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "threads": threads.items,
            "total": threads.total,
            "pages": threads.pages,
            "current_page": page
        }
    
    # ============================================================
    # WEBINARS
    # ============================================================
    
    def create_webinar(
        self,
        title: str,
        description: str,
        host_id: int,
        scheduled_at: datetime,
        duration_minutes: int,
        meeting_url: str,
        max_participants: Optional[int] = None,
        registration_required: bool = True
    ) -> int:
        """Create webinar event"""
        try:
            webinar = Webinar(
                title=title,
                description=description,
                host_id=host_id,
                scheduled_at=scheduled_at,
                duration_minutes=duration_minutes,
                meeting_url=meeting_url,
                max_participants=max_participants,
                registration_required=registration_required
            )
            db.session.add(webinar)
            db.session.commit()
            return webinar.id
        except Exception as e:
            logger.error(f"Create webinar error: {e}")
            db.session.rollback()
            return 0
    
    def register_for_webinar(self, webinar_id: int, user_id: int) -> bool:
        """Register user for webinar"""
        try:
            webinar = Webinar.query.get(webinar_id)
            if not webinar or not webinar.registration_required:
                return False
            
            # Check if already registered
            existing = WebinarRegistration.query.filter_by(
                webinar_id=webinar_id,
                user_id=user_id
            ).first()
            
            if existing:
                return True
            
            # Check capacity
            if webinar.max_participants:
                current_registrations = WebinarRegistration.query.filter_by(webinar_id=webinar_id).count()
                if current_registrations >= webinar.max_participants:
                    return False
            
            registration = WebinarRegistration(
                webinar_id=webinar_id,
                user_id=user_id
            )
            db.session.add(registration)
            db.session.commit()
            
            # Send confirmation notification
            self.create_notification(
                user_id,
                f"You're registered for: {webinar.title}",
                "webinar",
                f"/webinars/{webinar_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Webinar registration error: {e}")
            db.session.rollback()
            return False
    
    # ============================================================
    # SMS & WHATSAPP MESSAGING
    # ============================================================
    
    def send_sms(
        self,
        to_phone: str,
        message: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via Twilio
        
        Args:
            to_phone: Phone number in E.164 format (+1234567890)
            message: Message text (160 chars recommended)
            user_id: Optional user ID for tracking
        """
        if not twilio_client:
            logger.error("Twilio client not configured")
            return {"success": False, "error": "SMS service not available"}
        
        try:
            # Ensure phone number is in E.164 format
            if not to_phone.startswith('+'):
                to_phone = f'+1{to_phone}'  # Assume US if no country code
            
            # Send SMS
            sms = twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            logger.info(f"SMS sent to {to_phone}: {sms.sid}")
            
            # Track in database if user provided
            if user_id:
                notification = Notification(
                    recipient_id=user_id,
                    message=f"SMS sent: {message[:50]}...",
                    category="sms",
                    is_read=True
                )
                db.session.add(notification)
                db.session.commit()
            
            return {
                "success": True,
                "sid": sms.sid,
                "status": sms.status,
                "to": to_phone
            }
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        user_id: Optional[int] = None,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to_phone: Phone number in E.164 format (+1234567890)
            message: Message text
            user_id: Optional user ID for tracking
            media_url: Optional media attachment URL
        """
        if not twilio_client:
            logger.error("Twilio client not configured")
            return {"success": False, "error": "WhatsApp service not available"}
        
        try:
            # Format WhatsApp number
            if not to_phone.startswith('whatsapp:'):
                if not to_phone.startswith('+'):
                    to_phone = f'+1{to_phone}'
                to_phone = f'whatsapp:{to_phone}'
            
            # Prepare message params
            msg_params = {
                "body": message,
                "from_": TWILIO_WHATSAPP_NUMBER,
                "to": to_phone
            }
            
            if media_url:
                msg_params["media_url"] = [media_url]
            
            # Send WhatsApp message
            whatsapp = twilio_client.messages.create(**msg_params)
            
            logger.info(f"WhatsApp sent to {to_phone}: {whatsapp.sid}")
            
            # Track in database
            if user_id:
                notification = Notification(
                    recipient_id=user_id,
                    message=f"WhatsApp sent: {message[:50]}...",
                    category="whatsapp",
                    is_read=True
                )
                db.session.add(notification)
                db.session.commit()
            
            return {
                "success": True,
                "sid": whatsapp.sid,
                "status": whatsapp.status,
                "to": to_phone
            }
            
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_bulk_sms(
        self,
        phone_numbers: List[str],
        message: str
    ) -> Dict[str, Any]:
        """Send SMS to multiple recipients"""
        results = {
            "success": [],
            "failed": [],
            "total": len(phone_numbers)
        }
        
        for phone in phone_numbers:
            result = self.send_sms(phone, message)
            if result["success"]:
                results["success"].append(phone)
            else:
                results["failed"].append({"phone": phone, "error": result.get("error")})
        
        return results
    
    def send_notification_via_sms(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        urgent: bool = False
    ) -> Dict[str, Any]:
        """
        Send notification via SMS if user has enabled it
        
        Args:
            user_id: User ID
            notification_type: Type of notification (job_alert, deadline, etc.)
            message: Message text
            urgent: If true, send even if user has SMS disabled for this type
        """
        try:
            user = User.query.get(user_id)
            if not user or not user.phone:
                return {"success": False, "error": "User has no phone number"}
            
            # Check user preferences (would need NotificationPreference model)
            prefs = user.notification_preferences or {}
            sms_enabled = prefs.get(f"{notification_type}_sms", False)
            
            if not sms_enabled and not urgent:
                return {"success": False, "error": "SMS disabled for this notification type"}
            
            # Add urgency prefix
            if urgent:
                message = f"[URGENT] {message}"
            
            return self.send_sms(user.phone, message, user_id)
            
        except Exception as e:
            logger.error(f"SMS notification error: {e}")
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # SERIALIZATION HELPERS
    # ============================================================
    
    def _serialize_message(self, message: Message) -> Dict:
        return {
            "id": message.id,
            "sender": message.sender.full_name,
            "subject": message.subject,
            "body": message.body,
            "is_read": message.is_read,
            "created_at": message.created_at.isoformat(),
            "thread_id": message.thread_id
        }
    
    def _serialize_notification(self, notification: Notification) -> Dict:
        return {
            "id": notification.id,
            "message": notification.message,
            "category": notification.category,
            "link": notification.link,
            "is_read": notification.is_read,
            "timestamp": notification.timestamp.isoformat()
        }
    
    def _serialize_announcement(self, announcement: Announcement) -> Dict:
        return {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "priority": announcement.priority,
            "published_at": announcement.published_at.isoformat()
        }


# Import or_ for queries
from sqlalchemy import or_

# Singleton
_communication_service = None

def get_communication_service() -> CommunicationService:
    global _communication_service
    if _communication_service is None:
        _communication_service = CommunicationService()
    return _communication_service
