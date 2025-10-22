# =============================================================
# FILE: utils/mail_util.py
# PittState-Connect — Advanced Email Utility
# Supports HTML + plaintext emails, SendGrid API, and fallback SMTP.
# Used for confirmations, admin alerts, digests, and notifications.
# =============================================================

import os
import logging
from flask_mail import Message
from flask import current_app, render_template
import requests

log = logging.getLogger("mail_util")

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pittstate.edu")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@pittstateconnect.com")
APP_NAME = "PittState-Connect"

# -------------------------------------------------------------
# FLASK-MAIL fallback
# -------------------------------------------------------------
def send_via_flaskmail(subject, recipients, html_body, text_body=None):
    try:
        from app_pro import mail
        msg = Message(subject, sender=FROM_EMAIL, recipients=recipients)
        msg.body = text_body or html_body
        msg.html = html_body
        mail.send(msg)
        log.info("📧 Flask-Mail: Sent to %s", recipients)
        return True
    except Exception as e:
        log.error("❌ Flask-Mail failed: %s", e)
        return False


# -------------------------------------------------------------
# SENDGRID DELIVERY
# -------------------------------------------------------------
def send_via_sendgrid(subject, recipients, html_body, text_body=None):
    if not SENDGRID_API_KEY:
        return False

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": r} for r in recipients]}],
                "from": {"email": FROM_EMAIL, "name": APP_NAME},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text_body or ""},
                    {"type": "text/html", "value": html_body},
                ],
            },
            timeout=10,
        )
        if response.status_code in (200, 202):
            log.info("✅ SendGrid: Sent to %s", recipients)
            return True
        else:
            log.warning("⚠️ SendGrid response %s: %s", response.status_code, response.text)
            return False
    except Exception as e:
        log.error("❌ SendGrid error: %s", e)
        return False


# -------------------------------------------------------------
# MAIN SEND FUNCTION
# -------------------------------------------------------------
def send_email(subject, recipients, template_name=None, context=None, text_body=None):
    """Send an email using HTML template or plain text fallback."""
    context = context or {}
    html_body = None
    try:
        if template_name:
            html_body = render_template(template_name, **context)
    except Exception as e:
        log.error("❌ Template render failed: %s", e)

    # Fallback: simple plaintext message
    if not html_body:
        html_body = text_body or "(No content)"

    # Try SendGrid first, then fallback
    if SENDGRID_API_KEY:
        ok = send_via_sendgrid(subject, recipients, html_body, text_body)
        if ok:
            return True

    return send_via_flaskmail(subject, recipients, html_body, text_body)
