# =============================================================
# FILE: utils/mail_util.py
# Centralized email utility for PittState-Connect
# Supports plain text + HTML, multiple recipients,
# and safe fallbacks for Render deployments.
# =============================================================

import logging
from flask_mail import Message
from app_pro import mail
from flask import current_app

def send_email(subject: str, recipients: list, body: str, html: str = None):
    """Send an email via configured Flask-Mail."""
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        if html:
            msg.html = html
        mail.send(msg)
        current_app.logger.info(f"📧 Email sent successfully to {recipients}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        return False
