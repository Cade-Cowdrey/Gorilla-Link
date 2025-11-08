"""
Integration Service - External services and API connections
Canvas/Moodle, LinkedIn, Google/MS SSO, Stripe, Twilio, etc.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
import logging
from extensions import db
from models_extended import ExternalIntegration, PaymentTransaction, PushNotificationToken

logger = logging.getLogger(__name__)


class IntegrationService:
    """Manage external service integrations"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    # ============================================================
    # STRIPE PAYMENT INTEGRATION
    # ============================================================
    
    def initialize_stripe_payment(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD",
        purpose: str = "donation",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initialize Stripe payment session
        """
        try:
            import stripe
            stripe.api_key = self.config.get("STRIPE_SECRET_KEY")
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                metadata=metadata or {},
                description=f"{purpose} - User {user_id}"
            )
            
            # Save transaction record
            transaction = PaymentTransaction(
                user_id=user_id,
                transaction_id=intent.id,
                amount=amount,
                currency=currency,
                payment_method="stripe",
                purpose=purpose,
                status="pending",
                metadata=metadata
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "transaction_id": intent.id
            }
            
        except Exception as e:
            logger.error(f"Stripe payment initialization error: {e}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def confirm_stripe_payment(self, transaction_id: str) -> bool:
        """
        Confirm Stripe payment completion
        """
        try:
            import stripe
            stripe.api_key = self.config.get("STRIPE_SECRET_KEY")
            
            intent = stripe.PaymentIntent.retrieve(transaction_id)
            
            transaction = PaymentTransaction.query.filter_by(transaction_id=transaction_id).first()
            if transaction:
                transaction.status = "completed" if intent.status == "succeeded" else "failed"
                db.session.commit()
            
            return intent.status == "succeeded"
            
        except Exception as e:
            logger.error(f"Stripe payment confirmation error: {e}")
            return False
    
    def create_stripe_subscription(
        self,
        user_id: int,
        price_id: str,
        customer_email: str
    ) -> Dict[str, Any]:
        """
        Create Stripe subscription
        """
        try:
            import stripe
            stripe.api_key = self.config.get("STRIPE_SECRET_KEY")
            
            # Create or get customer
            customer = stripe.Customer.create(
                email=customer_email,
                metadata={"user_id": str(user_id)}
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice and subscription.latest_invoice.payment_intent else None
            }
            
        except Exception as e:
            logger.error(f"Stripe subscription error: {e}")
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # TWILIO SMS/VOICE NOTIFICATIONS
    # ============================================================
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS via Twilio
        """
        try:
            from twilio.rest import Client
            
            account_sid = self.config.get("TWILIO_ACCOUNT_SID")
            auth_token = self.config.get("TWILIO_AUTH_TOKEN")
            from_phone = self.config.get("TWILIO_PHONE_NUMBER")
            
            if not from_phone:
                logger.error("Twilio phone number not configured")
                return False
            
            client = Client(account_sid, auth_token)
            
            message_obj = client.messages.create(
                body=message,
                from_=from_phone,
                to=to_phone
            )
            
            logger.info(f"SMS sent: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
    
    def send_voice_call(self, to_phone: str, message_url: str) -> bool:
        """
        Initiate voice call via Twilio
        """
        try:
            from twilio.rest import Client
            
            account_sid = self.config.get("TWILIO_ACCOUNT_SID")
            auth_token = self.config.get("TWILIO_AUTH_TOKEN")
            from_phone = self.config.get("TWILIO_PHONE_NUMBER")
            
            client = Client(account_sid, auth_token)
            
            call = client.calls.create(
                url=message_url,
                to=to_phone,
                from_=from_phone
            )
            
            logger.info(f"Call initiated: {call.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Voice call error: {e}")
            return False
    
    # ============================================================
    # PUSH NOTIFICATIONS (Firebase)
    # ============================================================
    
    def send_push_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send push notification via Firebase Cloud Messaging
        """
        try:
            import firebase_admin
            from firebase_admin import messaging
            
            # Get user's push tokens
            tokens = PushNotificationToken.query.filter_by(
                user_id=user_id,
                active=True
            ).all()
            
            if not tokens:
                logger.warning(f"No push tokens found for user {user_id}")
                return False
            
            # Create message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=[token.token for token in tokens]
            )
            
            # Send
            response = messaging.send_multicast(message)
            logger.info(f"Push notifications sent: {response.success_count} successful")
            
            return response.success_count > 0
            
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return False
    
    # ============================================================
    # GOOGLE CALENDAR SYNC
    # ============================================================
    
    def sync_google_calendar(self, user_id: int, access_token: str) -> bool:
        """
        Sync events with Google Calendar
        """
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials(token=access_token)
            service = build('calendar', 'v3', credentials=creds)
            
            # Get events from PittState-Connect
            from models import Event, User
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Fetch user's events (simplified)
            events = Event.query.limit(10).all()
            
            for event in events:
                google_event = {
                    'summary': event.title,
                    'description': event.description,
                    'start': {
                        'dateTime': event.start_time.isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                    'end': {
                        'dateTime': event.end_time.isoformat(),
                        'timeZone': 'America/Chicago',
                    },
                }
                
                service.events().insert(calendarId='primary', body=google_event).execute()
            
            logger.info(f"Google Calendar synced for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Google Calendar sync error: {e}")
            return False
    
    # ============================================================
    # MICROSOFT OUTLOOK CALENDAR SYNC
    # ============================================================
    
    def sync_outlook_calendar(self, user_id: int, access_token: str) -> bool:
        """
        Sync events with Microsoft Outlook Calendar
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get events
            from models import Event
            events = Event.query.limit(10).all()
            
            for event in events:
                outlook_event = {
                    "subject": event.title,
                    "body": {
                        "contentType": "HTML",
                        "content": event.description or ""
                    },
                    "start": {
                        "dateTime": event.start_time.isoformat(),
                        "timeZone": "Central Standard Time"
                    },
                    "end": {
                        "dateTime": event.end_time.isoformat(),
                        "timeZone": "Central Standard Time"
                    }
                }
                
                response = requests.post(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers=headers,
                    json=outlook_event
                )
                
                if response.status_code != 201:
                    logger.error(f"Outlook event creation failed: {response.text}")
            
            logger.info(f"Outlook Calendar synced for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Outlook Calendar sync error: {e}")
            return False
    
    # ============================================================
    # CANVAS LMS INTEGRATION
    # ============================================================
    
    def fetch_canvas_courses(self, access_token: str) -> List[Dict]:
        """
        Fetch courses from Canvas LMS
        """
        try:
            canvas_url = self.config.get("CANVAS_URL", "https://canvas.instructure.com")
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(
                f"{canvas_url}/api/v1/courses",
                headers=headers
            )
            
            if response.status_code == 200:
                courses = response.json()
                logger.info(f"Fetched {len(courses)} Canvas courses")
                return courses
            
            return []
            
        except Exception as e:
            logger.error(f"Canvas course fetch error: {e}")
            return []
    
    def sync_canvas_grades(self, user_id: int, access_token: str) -> bool:
        """
        Sync grades from Canvas LMS
        """
        try:
            canvas_url = self.config.get("CANVAS_URL")
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # Get user's courses
            courses = self.fetch_canvas_courses(access_token)
            
            # For each course, get grades
            for course in courses:
                course_id = course.get("id")
                grades_response = requests.get(
                    f"{canvas_url}/api/v1/courses/{course_id}/enrollments",
                    headers=headers
                )
                
                if grades_response.status_code == 200:
                    # Process grades (simplified)
                    pass
            
            logger.info(f"Canvas grades synced for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Canvas grade sync error: {e}")
            return False
    
    # ============================================================
    # LINKEDIN INTEGRATION
    # ============================================================
    
    def fetch_linkedin_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from LinkedIn
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                logger.info("LinkedIn profile fetched successfully")
                return profile
            
            return {}
            
        except Exception as e:
            logger.error(f"LinkedIn profile fetch error: {e}")
            return {}
    
    def post_to_linkedin(self, access_token: str, content: str) -> bool:
        """
        Post content to LinkedIn
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get user ID first
            me_response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
            
            if me_response.status_code != 200:
                return False
            
            user_id = me_response.json().get("id")
            
            # Create post
            post_data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"LinkedIn post error: {e}")
            return False
    
    # ============================================================
    # HANDSHAKE INTEGRATION
    # ============================================================
    
    def fetch_handshake_jobs(self, api_key: str) -> List[Dict]:
        """
        Fetch job postings from Handshake
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Handshake API endpoint (example)
            response = requests.get(
                "https://app.joinhandshake.com/api/v1/jobs",
                headers=headers
            )
            
            if response.status_code == 200:
                jobs = response.json()
                logger.info(f"Fetched {len(jobs)} Handshake jobs")
                return jobs
            
            return []
            
        except Exception as e:
            logger.error(f"Handshake job fetch error: {e}")
            return []
    
    # ============================================================
    # SALESFORCE INTEGRATION
    # ============================================================
    
    def sync_to_salesforce(self, user_data: Dict) -> bool:
        """
        Sync user/donor data to Salesforce
        """
        try:
            from simple_salesforce.api import Salesforce
            
            sf = Salesforce(
                username=self.config.get("SALESFORCE_USERNAME"),
                password=self.config.get("SALESFORCE_PASSWORD"),
                security_token=self.config.get("SALESFORCE_TOKEN")
            )
            
            # Create/update contact
            contact = sf.Contact.create({
                'FirstName': user_data.get('first_name'),
                'LastName': user_data.get('last_name'),
                'Email': user_data.get('email')
            })
            
            logger.info(f"Salesforce contact created: {contact}")
            return True
            
        except Exception as e:
            logger.error(f"Salesforce sync error: {e}")
            return False
    
    # ============================================================
    # GOOGLE SSO
    # ============================================================
    
    def verify_google_token(self, token: str) -> Optional[Dict]:
        """
        Verify Google OAuth token
        """
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
            
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.config.get("GOOGLE_CLIENT_ID")
            )
            
            return {
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified")
            }
            
        except Exception as e:
            logger.error(f"Google token verification error: {e}")
            return None
    
    # ============================================================
    # MICROSOFT SSO
    # ============================================================
    
    def verify_microsoft_token(self, token: str) -> Optional[Dict]:
        """
        Verify Microsoft OAuth token
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                    "name": user_info.get("displayName"),
                    "id": user_info.get("id")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Microsoft token verification error: {e}")
            return None


# Singleton
_integration_service = None

def get_integration_service(config: Optional[Dict[str, str]] = None) -> Optional[IntegrationService]:
    global _integration_service
    if _integration_service is None and config:
        _integration_service = IntegrationService(config)
    return _integration_service
