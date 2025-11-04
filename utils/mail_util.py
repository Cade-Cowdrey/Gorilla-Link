"""
PittState-Connect | Mail Utility
Handles SendGrid or Flask-Mail sending and fallback alerts.
"""

import os
import datetime
from flask_mail import Message
from extensions import mail
from loguru import logger


def send_email(subject, recipients, html_body, sender=None):
    """Primary email sending function."""
    try:
        msg = Message(subject, recipients=recipients, sender=sender or os.getenv("MAIL_DEFAULT_SENDER"))
        msg.html = html_body
        mail.send(msg)
        logger.info(f"📧 Email sent successfully: {subject} → {recipients}")
    except Exception as e:
        logger.error(f"❌ send_email failed: {e}")


def send_system_alert(subject: str, body: str, recipient_email: str = None) -> bool:
    """
    Send urgent system alert email to administrators.
    
    Args:
        subject: Alert subject line
        body: Alert message body (plain text or HTML)
        recipient_email: Override default admin email
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from flask import current_app
        
        # Determine recipient
        recipient = recipient_email or current_app.config.get("ADMIN_EMAIL", "admin@pittstate.edu")
        
        # Check if mail is configured
        if not hasattr(current_app, 'extensions') or 'mail' not in current_app.extensions:
            logger.warning(f"⚠️ Flask-Mail not configured. System alert logged but not emailed: {subject}")
            logger.warning(f"Alert body: {body}")
            return False
        
        # Build HTML email with urgent styling
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .alert-container {{ max-width: 600px; margin: 0 auto; background-color: white; border: 4px solid #dc3545; border-radius: 8px; overflow: hidden; }}
                .alert-header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; text-align: center; }}
                .alert-icon {{ font-size: 48px; margin-bottom: 10px; }}
                .alert-title {{ font-size: 24px; font-weight: bold; margin: 0; }}
                .alert-body {{ padding: 30px; line-height: 1.6; color: #333; }}
                .alert-footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; }}
                .timestamp {{ font-weight: bold; color: #495057; margin-bottom: 15px; }}
            </style>
        </head>
        <body>
            <div class="alert-container">
                <div class="alert-header">
                    <div class="alert-icon">🚨</div>
                    <h1 class="alert-title">System Alert</h1>
                </div>
                <div class="alert-body">
                    <div class="timestamp">⏰ {datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}</div>
                    <h2 style="color: #dc3545; margin-top: 0;">{subject}</h2>
                    <div>{body}</div>
                </div>
                <div class="alert-footer">
                    This is an automated system alert from PittState Connect.
                    <br>Please do not reply to this email.
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create and send message
        from flask_mail import Message
        msg = Message(
            subject=f"🚨 SYSTEM ALERT: {subject}",
            recipients=[recipient],
            html=html_body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@pittstate.edu")
        )
        
        mail = current_app.extensions['mail']
        mail.send(msg)
        
        logger.info(f"✅ System alert email sent successfully to {recipient}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send system alert email: {str(e)}")
        logger.error(f"Alert subject: {subject}")
        logger.error(f"Alert body: {body}")
        
        # Fallback: Write to file for manual review
        try:
            alert_log_path = "logs/system_alerts.log"
            os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)
            
            with open(alert_log_path, "a") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TIMESTAMP: {datetime.datetime.now().isoformat()}\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(f"BODY: {body}\n")
                f.write(f"ERROR: {str(e)}\n")
                f.write(f"{'='*80}\n")
            
            logger.warning(f"⚠️ System alert logged to {alert_log_path}")
        except Exception as log_error:
            logger.error(f"Failed to write alert to log file: {str(log_error)}")
        
        return False
