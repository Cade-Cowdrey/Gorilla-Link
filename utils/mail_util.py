"""
PittState-Connect | Mail Utility
Handles SendGrid or Flask-Mail sending and fallback alerts.
"""

import os
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


def send_system_alert(subject, body):
    """Stub fallback system alert (logs instead of emailing)."""
    logger.warning(f"⚠️ SYSTEM ALERT: {subject} | {body}")
