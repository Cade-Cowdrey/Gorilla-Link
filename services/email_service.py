"""
Email Notification System
Flask-Mail integration for sending automated emails
"""
from flask import render_template, current_app
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import os

mail = Mail()

class EmailNotificationService:
    """Handles all email notifications"""
    
    def __init__(self):
        self.from_email = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@pittstate-connect.com')
        self.from_name = 'Gorilla-Link - PSU Connect'
    
    def send_appointment_confirmation(self, appointment):
        """
        Send confirmation email when appointment is booked
        
        Args:
            appointment: CareerServiceAppointment model instance
        """
        try:
            student = appointment.student
            advisor = appointment.advisor
            
            subject = f'Appointment Confirmed - {appointment.scheduled_at.strftime("%b %d, %Y")}'
            
            html_body = render_template(
                'emails/appointment_confirmation.html',
                student=student,
                advisor=advisor,
                appointment=appointment
            )
            
            text_body = f"""
Appointment Confirmation
========================

Hello {student.first_name},

Your career services appointment has been confirmed!

Date: {appointment.scheduled_at.strftime('%A, %B %d, %Y')}
Time: {appointment.scheduled_at.strftime('%I:%M %p')}
Duration: {appointment.duration_minutes} minutes
Advisor: {advisor.first_name} {advisor.last_name}
Type: {appointment.appointment_type.replace('_', ' ').title()}
Location: {appointment.location}

We look forward to seeing you!

- Gorilla-Link Team
"""
            
            self._send_email(
                recipient=student.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='appointment_confirmation',
                user_id=student.id,
                related_entity_type='appointment',
                related_entity_id=appointment.id
            )
            
            logger.info(f"Sent appointment confirmation to {student.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {e}")
            return False
    
    def send_appointment_reminder(self, appointment):
        """
        Send 24-hour reminder before appointment
        
        Args:
            appointment: CareerServiceAppointment model instance
        """
        try:
            student = appointment.student
            advisor = appointment.advisor
            
            subject = f'Reminder: Appointment Tomorrow at {appointment.scheduled_at.strftime("%I:%M %p")}'
            
            html_body = render_template(
                'emails/appointment_reminder.html',
                student=student,
                advisor=advisor,
                appointment=appointment
            )
            
            text_body = f"""
Appointment Reminder
===================

Hello {student.first_name},

This is a friendly reminder about your upcoming appointment:

Tomorrow at {appointment.scheduled_at.strftime('%I:%M %p')}
With: {advisor.first_name} {advisor.last_name}
Location: {appointment.location}

Please arrive 5 minutes early. If you need to cancel or reschedule, please do so at least 2 hours in advance.

Visit: https://pittstate-connect.onrender.com/appointments/

- Gorilla-Link Team
"""
            
            self._send_email(
                recipient=student.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='appointment_reminder',
                user_id=student.id,
                related_entity_type='appointment',
                related_entity_id=appointment.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {e}")
            return False
    
    def send_appointment_feedback_request(self, appointment):
        """
        Request feedback after completed appointment
        
        Args:
            appointment: CareerServiceAppointment model instance
        """
        try:
            student = appointment.student
            
            subject = 'How was your appointment? Share your feedback'
            
            feedback_url = f"https://pittstate-connect.onrender.com/appointments/{appointment.id}/feedback"
            
            html_body = render_template(
                'emails/appointment_feedback.html',
                student=student,
                appointment=appointment,
                feedback_url=feedback_url
            )
            
            text_body = f"""
Feedback Request
===============

Hello {student.first_name},

Thank you for meeting with our Career Services team! We'd love to hear about your experience.

Please take 2 minutes to share your feedback:
{feedback_url}

Your input helps us improve our services.

- Gorilla-Link Team
"""
            
            self._send_email(
                recipient=student.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='appointment_feedback_request',
                user_id=student.id,
                related_entity_type='appointment',
                related_entity_id=appointment.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending feedback request: {e}")
            return False
    
    def send_scholarship_match_alert(self, user, scholarships: List):
        """
        Notify student of new scholarship matches
        
        Args:
            user: User model instance
            scholarships: List of ScholarshipMatch instances
        """
        try:
            total_amount = sum([s.amount for s in scholarships if s.amount])
            
            subject = f'{len(scholarships)} New Scholarship Matches - ${total_amount:,} Available!'
            
            html_body = render_template(
                'emails/scholarship_matches.html',
                user=user,
                scholarships=scholarships,
                total_amount=total_amount
            )
            
            text_body = f"""
New Scholarship Matches!
=======================

Hello {user.first_name},

Great news! We found {len(scholarships)} new scholarships you're eligible for, totaling ${total_amount:,}!

Top Matches:
"""
            for scholarship in scholarships[:3]:
                text_body += f"\n- {scholarship.title}: ${scholarship.amount:,} (Deadline: {scholarship.deadline.strftime('%b %d, %Y')})"
            
            text_body += "\n\nView all matches: https://pittstate-connect.onrender.com/scholarships/\n\n- Gorilla-Link Team"
            
            self._send_email(
                recipient=user.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='scholarship_match',
                user_id=user.id
            )
            
            logger.info(f"Sent scholarship matches to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending scholarship matches: {e}")
            return False
    
    def send_job_alert(self, user, jobs: List):
        """
        Notify student of new job matches
        
        Args:
            user: User model instance
            jobs: List of Job instances
        """
        try:
            subject = f'{len(jobs)} New Job Opportunities Match Your Profile'
            
            html_body = render_template(
                'emails/job_alerts.html',
                user=user,
                jobs=jobs
            )
            
            text_body = f"""
New Job Opportunities
=====================

Hello {user.first_name},

We found {len(jobs)} new jobs that match your profile!

Featured Jobs:
"""
            for job in jobs[:3]:
                salary_range = f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min else "Competitive"
                text_body += f"\n- {job.title} at {job.company}: {salary_range}"
            
            text_body += "\n\nView all jobs: https://pittstate-connect.onrender.com/careers/\n\n- Gorilla-Link Team"
            
            self._send_email(
                recipient=user.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='job_alert',
                user_id=user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending job alerts: {e}")
            return False
    
    def send_welcome_email(self, user):
        """
        Send welcome email to new users
        
        Args:
            user: User model instance
        """
        try:
            subject = 'Welcome to Gorilla-Link - Let\'s Get Started!'
            
            html_body = render_template(
                'emails/welcome.html',
                user=user
            )
            
            text_body = f"""
Welcome to Gorilla-Link!
========================

Hello {user.first_name},

Welcome to Pittsburg State University's career and alumni platform! We're excited to have you.

Here's what you can do:

✓ Find scholarships worth thousands of dollars
✓ Browse job opportunities from top employers
✓ Book career advising appointments
✓ Connect with 15,000+ PSU alumni
✓ Track your career progress

Get Started:
1. Complete your profile: https://pittstate-connect.onrender.com/profile/
2. Browse scholarships: https://pittstate-connect.onrender.com/scholarships/
3. Book an appointment: https://pittstate-connect.onrender.com/appointments/

Need help? Reply to this email anytime.

GO GORILLAS!
- Gorilla-Link Team
"""
            
            self._send_email(
                recipient=user.email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                notification_type='welcome',
                user_id=user.id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False
    
    def send_admin_alert(self, admin_emails: List[str], alert_message: str, alert_type: str = 'info'):
        """
        Send alert to administrators
        
        Args:
            admin_emails: List of admin email addresses
            alert_message: Alert message
            alert_type: Type of alert (info, warning, critical)
        """
        try:
            subject_prefix = {
                'info': '[INFO]',
                'warning': '[WARNING]',
                'critical': '[CRITICAL]'
            }.get(alert_type, '[INFO]')
            
            subject = f'{subject_prefix} Gorilla-Link Platform Alert'
            
            text_body = f"""
Platform Alert
=============

{alert_message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Dashboard: https://pittstate-connect.onrender.com/admin/

- Gorilla-Link System
"""
            
            for admin_email in admin_emails:
                self._send_email(
                    recipient=admin_email,
                    subject=subject,
                    text_body=text_body,
                    notification_type='admin_alert'
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin alert: {e}")
            return False
    
    def _send_email(self, 
                   recipient: str, 
                   subject: str, 
                   text_body: str, 
                   html_body: str = None,
                   notification_type: str = 'general',
                   user_id: int = None,
                   related_entity_type: str = None,
                   related_entity_id: int = None):
        """
        Internal method to send email and log to database
        
        Args:
            recipient: Email address
            subject: Email subject
            text_body: Plain text body
            html_body: HTML body (optional)
            notification_type: Type of notification
            user_id: User ID for tracking
            related_entity_type: Type of related entity
            related_entity_id: ID of related entity
        """
        try:
            # Create message
            msg = Message(
                subject=subject,
                sender=(self.from_name, self.from_email),
                recipients=[recipient]
            )
            
            msg.body = text_body
            if html_body:
                msg.html = html_body
            
            # Send email
            mail.send(msg)
            
            # Log to database
            if user_id:
                from models import db
                from models_growth_features import EmailNotification
                
                notification = EmailNotification(
                    user_id=user_id,
                    notification_type=notification_type,
                    subject=subject,
                    body=text_body,
                    recipient_email=recipient,
                    status='sent',
                    sent_at=datetime.utcnow(),
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id
                )
                db.session.add(notification)
                db.session.commit()
            
            logger.info(f"Sent {notification_type} email to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            
            # Log failed email
            if user_id:
                from models import db
                from models_growth_features import EmailNotification
                
                try:
                    notification = EmailNotification(
                        user_id=user_id,
                        notification_type=notification_type,
                        subject=subject,
                        body=text_body,
                        recipient_email=recipient,
                        status='failed',
                        error_message=str(e),
                        related_entity_type=related_entity_type,
                        related_entity_id=related_entity_id
                    )
                    db.session.add(notification)
                    db.session.commit()
                except Exception:
                    pass
            
            return False


# Singleton instance
email_service = EmailNotificationService()


def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)
