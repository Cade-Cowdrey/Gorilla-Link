# utils/mail_util.py
# ---------------------------------------------------------------------
# Production-ready mail utility for PittState-Connect
# - Supports HTML + plaintext emails
# - send_system_alert for admins
# - PSU-branded templates and logging
# - Graceful fallbacks if mail server unavailable
# ---------------------------------------------------------------------

import os
import logging
from flask_mail import Message
from flask import current_app, render_template
from smtplib import SMTPException
from datetime import datetime

# ---------------------------------------------------------------------
# Flask-Mail object is initialized in app_pro.py and imported via extensions
# ---------------------------------------------------------------------
from extensions import mail

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | mail_util | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# Configurable admin addresses
# ---------------------------------------------------------------------
ADMIN_EMAILS = [
    os.getenv("ADMIN_EMAIL", "psuconnect-admin@pittstate.edu"),
]
SYSTEM_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstateconnect.com")

# ---------------------------------------------------------------------
# PSU-branded footer (used for HTML)
# ---------------------------------------------------------------------
PSU_FOOTER_HTML = """
<br><br>
<hr style='border:0;border-top:1px solid #ddd;margin-top:20px;margin-bottom:10px;'>
<p style='font-size:12px;color:#888;'>
  <strong>PittState-Connect</strong><br>
  Empowering Gorillas — Connecting Students, Alumni, and Employers.<br>
  &copy; {year} Pittsburg State University. All rights reserved.
</p>
"""

# ---------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------
def send_html_email(subject, recipients, html_body, text_body=None, sender=None, cc=None, bcc=None):
    """
    Send an email with both HTML and plaintext bodies.
    Automatically logs success/failure and returns True/False.
    """
    sender = sender or SYSTEM_SENDER
    text_body = text_body or strip_html_tags(html_body)

    try:
        msg = Message(
            subject=subject,
            sender=sender,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            body=text_body,
            html=html_body + PSU_FOOTER_HTML.format(year=datetime.now().year),
        )
        mail.send(msg)
        logger.info(f"✅ Email sent to {recipients} | Subject: {subject}")
        return True
    except SMTPException as e:
        logger.error(f"❌ SMTPException sending email '{subject}': {e}")
        return False
    except Exception as e:
        logger.exception(f"❌ Unknown error sending email '{subject}': {e}")
        return False


# ---------------------------------------------------------------------
# Utility: strip HTML for plaintext fallback
# ---------------------------------------------------------------------
def strip_html_tags(html_text):
    """Rudimentary HTML tag stripper for plaintext bodies."""
    import re
    clean = re.compile("<.*?>")
    return re.sub(clean, "", html_text)


# ---------------------------------------------------------------------
# System alert: used by utils.ai_util or any critical failure
# ---------------------------------------------------------------------
def send_system_alert(title: str, message: str):
    """
    Send a critical system alert to admin(s).
    Called automatically by API / AI / Scheduler when errors occur.
    """
    subject = f"🚨 PSU-Connect Alert: {title}"
    html = f"""
    <h3 style='color:#b71c1c;'>System Alert</h3>
    <p><strong>Event:</strong> {title}</p>
    <p><strong>Message:</strong><br>{message}</p>
    <p><strong>Time (UTC):</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

    logger.warning(f"⚠️ Sending system alert: {title}")
    ok = send_html_email(subject, ADMIN_EMAILS, html)

    if not ok:
        logger.error("❌ System alert failed to send (mail server unavailable).")
    return ok


# ---------------------------------------------------------------------
# Optional enhancement: user notifications (email + in-app)
# ---------------------------------------------------------------------
def send_user_notification(user, subject: str, message: str, html_template: str = None, **kwargs):
    """
    Sends PSU-branded notification to a user.
    If html_template is provided, renders from /templates/emails/.
    """
    try:
        if html_template:
            html_body = render_template(html_template, user=user, message=message, **kwargs)
        else:
            html_body = f"<p>{message}</p>"

        recipients = [user.email]
        send_html_email(subject, recipients, html_body)
        logger.info(f"📧 User notification sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send user notification to {getattr(user, 'email', 'unknown')}: {e}")
        return False
