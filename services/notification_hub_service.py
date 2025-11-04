"""
Notification Hub Service
Centralized notification routing, preferences, and delivery
"""

from typing import Dict, Any, List, Optional
from extensions import db, celery
from models import User, Notification
from models_extended import PushNotificationToken, Message
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class NotificationHubService:
    """Centralized notification management"""
    
    NOTIFICATION_TYPES = {
        # Platform notifications
        "new_post": {"channels": ["in_app", "push"], "priority": "low"},
        "new_comment": {"channels": ["in_app", "email", "push"], "priority": "medium"},
        "new_connection": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "connection_accepted": {"channels": ["in_app", "push"], "priority": "high"},
        
        # Scholarship notifications
        "scholarship_deadline": {"channels": ["in_app", "email", "sms", "push"], "priority": "critical"},
        "scholarship_matched": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "application_submitted": {"channels": ["in_app", "email"], "priority": "high"},
        "application_status": {"channels": ["in_app", "email", "push"], "priority": "high"},
        
        # Event notifications
        "event_reminder": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "event_cancelled": {"channels": ["in_app", "email", "sms", "push"], "priority": "critical"},
        "new_event": {"channels": ["in_app", "push"], "priority": "medium"},
        
        # Career notifications
        "new_job": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "job_application_viewed": {"channels": ["in_app"], "priority": "low"},
        "job_deadline": {"channels": ["in_app", "email"], "priority": "high"},
        
        # Mentorship notifications
        "mentorship_request": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "mentorship_accepted": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "session_scheduled": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "session_reminder": {"channels": ["in_app", "push"], "priority": "medium"},
        
        # System notifications
        "system_maintenance": {"channels": ["in_app", "email"], "priority": "critical"},
        "security_alert": {"channels": ["in_app", "email", "sms"], "priority": "critical"},
        "account_verification": {"channels": ["email"], "priority": "critical"},
        "password_reset": {"channels": ["email", "sms"], "priority": "critical"},
        
        # Communication notifications
        "new_message": {"channels": ["in_app", "email", "push"], "priority": "high"},
        "announcement": {"channels": ["in_app", "email"], "priority": "medium"},
        "forum_reply": {"channels": ["in_app", "email"], "priority": "low"},
        "webinar_reminder": {"channels": ["in_app", "email", "push"], "priority": "high"},
    }
    
    # ============================================================
    # NOTIFICATION ROUTING
    # ============================================================
    
    def send(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        link: Optional[str] = None,
        override_channels: Optional[List[str]] = None,
        override_priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification through appropriate channels based on type and user preferences
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            # Get notification config
            config = self.NOTIFICATION_TYPES.get(notification_type, {
                "channels": ["in_app"],
                "priority": "medium"
            })
            
            channels = override_channels or config["channels"]
            priority = override_priority or config["priority"]
            
            # Get user preferences
            preferences = user.notification_preferences or {}
            
            # Filter channels based on preferences
            enabled_channels = []
            for channel in channels:
                pref_key = f"{notification_type}_{channel}"
                if preferences.get(pref_key, True):  # Default to enabled
                    enabled_channels.append(channel)
            
            # If no channels enabled, at least use in-app
            if not enabled_channels and "in_app" in channels:
                enabled_channels = ["in_app"]
            
            results = {}
            
            # Send through each channel
            for channel in enabled_channels:
                if channel == "in_app":
                    results["in_app"] = self._send_in_app(
                        user_id, title, message, notification_type, link, data
                    )
                elif channel == "email":
                    results["email"] = self._send_email_notification(
                        user, title, message, data
                    )
                elif channel == "push":
                    results["push"] = self._send_push_notification(
                        user_id, title, message, data
                    )
                elif channel == "sms":
                    results["sms"] = self._send_sms_notification(
                        user, title, message
                    )
            
            logger.info(f"Notification sent to user {user_id}: {notification_type}")
            
            return {
                "success": True,
                "user_id": user_id,
                "type": notification_type,
                "priority": priority,
                "channels": enabled_channels,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Notification send error: {e}")
            return {"error": str(e)}
    
    def _send_in_app(
        self,
        user_id: int,
        title: str,
        message: str,
        category: str,
        link: Optional[str],
        data: Optional[Dict]
    ) -> bool:
        """Send in-app notification"""
        try:
            notification = Notification(
                user_id=user_id,
                message=f"{title}: {message}",
                category=category,
                link=link
            )
            db.session.add(notification)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"In-app notification error: {e}")
            db.session.rollback()
            return False
    
    def _send_email_notification(self, user: User, title: str, message: str, data: Optional[Dict]) -> bool:
        """Send email notification (async)"""
        try:
            from tasks.celery_tasks import send_async_email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #A50021;">{title}</h2>
                    <p>{message}</p>
                    {f"<p><a href='{data.get('link')}' style='color: #A50021;'>View Details</a></p>" if data and 'link' in data else ""}
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        Pittsburg State University - PittState Connect
                    </p>
                </div>
            </body>
            </html>
            """
            
            send_async_email.delay(
                to=user.email,
                subject=title,
                body=message,
                html=html
            )
            return True
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return False
    
    def _send_push_notification(self, user_id: int, title: str, message: str, data: Optional[Dict]) -> bool:
        """Send push notification (async)"""
        try:
            from tasks.celery_tasks import send_push_notification
            
            send_push_notification.delay(
                user_id=user_id,
                title=title,
                body=message,
                data=data or {}
            )
            return True
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return False
    
    def _send_sms_notification(self, user: User, title: str, message: str) -> bool:
        """Send SMS notification"""
        try:
            if not user.phone:
                return False
            
            from services.integration_service import get_integration_service
            integration = get_integration_service()
            
            sms_message = f"{title}: {message}"
            integration.send_sms(user.phone, sms_message)
            return True
        except Exception as e:
            logger.error(f"SMS notification error: {e}")
            return False
    
    # ============================================================
    # BATCH NOTIFICATIONS
    # ============================================================
    
    def send_bulk(
        self,
        user_ids: List[int],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification to multiple users
        """
        try:
            results = {
                "total": len(user_ids),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for user_id in user_ids:
                result = self.send(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data,
                    link=link
                )
                
                if result.get("success"):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": user_id,
                        "error": result.get("error")
                    })
            
            logger.info(f"Bulk notification sent: {results['successful']}/{results['total']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Bulk notification error: {e}")
            return {"error": str(e)}
    
    def send_to_role(
        self,
        role: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification to all users with a specific role
        """
        try:
            from models import Role
            
            role_obj = Role.query.filter_by(name=role).first()
            if not role_obj:
                return {"error": f"Role '{role}' not found"}
            
            user_ids = [user.id for user in role_obj.users]
            
            return self.send_bulk(
                user_ids=user_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                link=link
            )
            
        except Exception as e:
            logger.error(f"Role notification error: {e}")
            return {"error": str(e)}
    
    def send_to_department(
        self,
        department_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification to all users in a department
        """
        try:
            users = User.query.filter_by(department_id=department_id).all()
            user_ids = [user.id for user in users]
            
            return self.send_bulk(
                user_ids=user_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                link=link
            )
            
        except Exception as e:
            logger.error(f"Department notification error: {e}")
            return {"error": str(e)}
    
    # ============================================================
    # NOTIFICATION PREFERENCES
    # ============================================================
    
    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user notification preferences"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            preferences = user.notification_preferences or {}
            
            # Build preferences structure
            structured = {}
            for notif_type, config in self.NOTIFICATION_TYPES.items():
                structured[notif_type] = {}
                for channel in config["channels"]:
                    pref_key = f"{notif_type}_{channel}"
                    structured[notif_type][channel] = preferences.get(pref_key, True)
            
            return {
                "user_id": user_id,
                "preferences": structured,
                "email": user.email,
                "phone": user.phone,
                "has_push_tokens": PushNotificationToken.query.filter_by(user_id=user_id).count() > 0
            }
            
        except Exception as e:
            logger.error(f"Get preferences error: {e}")
            return {"error": str(e)}
    
    def update_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Dict[str, bool]]
    ) -> bool:
        """
        Update user notification preferences
        Format: {notification_type: {channel: enabled}}
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Flatten preferences
            flat_prefs = {}
            for notif_type, channels in preferences.items():
                for channel, enabled in channels.items():
                    pref_key = f"{notif_type}_{channel}"
                    flat_prefs[pref_key] = enabled
            
            user.notification_preferences = flat_prefs
            db.session.commit()
            
            logger.info(f"Notification preferences updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Update preferences error: {e}")
            db.session.rollback()
            return False
    
    def enable_channel(self, user_id: int, channel: str) -> bool:
        """Enable a notification channel for all notification types"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            preferences = user.notification_preferences or {}
            
            for notif_type in self.NOTIFICATION_TYPES.keys():
                pref_key = f"{notif_type}_{channel}"
                preferences[pref_key] = True
            
            user.notification_preferences = preferences
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Enable channel error: {e}")
            db.session.rollback()
            return False
    
    def disable_channel(self, user_id: int, channel: str) -> bool:
        """Disable a notification channel for all notification types"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            preferences = user.notification_preferences or {}
            
            for notif_type in self.NOTIFICATION_TYPES.keys():
                pref_key = f"{notif_type}_{channel}"
                preferences[pref_key] = False
            
            user.notification_preferences = preferences
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Disable channel error: {e}")
            db.session.rollback()
            return False
    
    # ============================================================
    # NOTIFICATION HISTORY & ANALYTICS
    # ============================================================
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user notification history"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            if category:
                query = query.filter_by(category=category)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
            
            return [{
                "id": n.id,
                "message": n.message,
                "category": n.category,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications]
            
        except Exception as e:
            logger.error(f"Get notifications error: {e}")
            return []
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Mark as read error: {e}")
            db.session.rollback()
            return False
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        try:
            Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({"is_read": True})
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Mark all as read error: {e}")
            db.session.rollback()
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
    
    def get_notification_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            total = Notification.query.filter(
                Notification.created_at >= cutoff
            ).count()
            
            by_category = db.session.query(
                Notification.category,
                db.func.count(Notification.id)
            ).filter(
                Notification.created_at >= cutoff
            ).group_by(Notification.category).all()
            
            read_rate = db.session.query(
                db.func.count(Notification.id).filter(Notification.is_read == True),
                db.func.count(Notification.id)
            ).filter(
                Notification.created_at >= cutoff
            ).first()
            
            return {
                "period_days": days,
                "total_sent": total,
                "by_category": {cat: count for cat, count in by_category},
                "read_count": read_rate[0] if read_rate else 0,
                "unread_count": (read_rate[1] - read_rate[0]) if read_rate else 0,
                "read_rate": (read_rate[0] / read_rate[1] * 100) if read_rate and read_rate[1] > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Notification stats error: {e}")
            return {"error": str(e)}


# Singleton
_notification_hub_service = None

def get_notification_hub_service() -> NotificationHubService:
    global _notification_hub_service
    if _notification_hub_service is None:
        _notification_hub_service = NotificationHubService()
    return _notification_hub_service
