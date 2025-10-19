"""
utils.mail_util
Safe mail utilities that won't break imports in production without SMTP.
They log actions and return True. If Flask-Mail is configured, they attempt to send.
"""

from typing import Iterable, Optional
import logging
from flask import current_app

try:
    from flask_mail import Message
    mail_available = True
except Exception:  # pragma: no cover
    Message = object  # type: ignore
    mail_available = False


def _send(subject: str, recipients: Iterable[str], body: str, html: Optional[str] = None) -> bool:
    """Internal helper: try to send via Flask-Mail; otherwise just log."""
    try:
        app = current_app._get_current_object()  # raises if no app context
    except Exception:
        logging.getLogger(__name__).warning("mail_util called without app context; logging only.")
        logging.getLogger(__name__).info("MAIL FAKED: %s -> %s\n%s", subject, list(recipients), body)
        return True

    logger = app.logger

    if not mail_available or "mail" not in app.extensions:
        logger.info("📧 (fake) %s -> %s", subject, list(recipients))
        logger.debug("Body: %s", body)
        return True

    try:
        mail = app.extensions["mail"]
        msg = Message(subject=subject, recipients=list(recipients), body=body, html=html)
        mail.send(msg)
        logger.info("📧 Sent: %s -> %s", subject, list(recipients))
        return True
    except Exception as e:  # pragma: no cover
        logger.exception("Failed to send email: %s", e)
        return False


# ---- Public functions expected by blueprints ----

def send_welcome_email(email: str, name: str = "Gorilla") -> bool:
    subject = "Welcome to PittState-Connect 🎉"
    body = f"Hi {name},\n\nWelcome to PittState-Connect!\n\n— PSU Team"
    return _send(subject, [email], body)


def send_verification_email(email: str, token: str) -> bool:
    verify_url = f"https://pittstate-connect.onrender.com/verify/{token}"
    subject = "Verify your PittState-Connect email"
    body = f"Click to verify: {verify_url}"
    html = f'<p>Click to verify: <a href="{verify_url}">{verify_url}</a></p>'
    return _send(subject, [email], body, html)


def send_password_reset_email(email: str, token: str) -> bool:
    reset_url = f"https://pittstate-connect.onrender.com/reset/{token}"
    subject = "Reset your PittState-Connect password"
    body = f"Reset link: {reset_url}"
    html = f'<p>Reset link: <a href="{reset_url}">{reset_url}</a></p>'
    return _send(subject, [email], body, html)


def send_weekly_digest_students(recipients: Iterable[str]) -> bool:
    subject = "Weekly Student Digest"
    body = "Here are this week’s highlights for students."
    return _send(subject, recipients, body)


def send_weekly_digest_alumni(recipients: Iterable[str]) -> bool:
    subject = "Weekly Alumni Digest"
    body = "Here are this week’s highlights for alumni."
    return _send(subject, recipients, body)


def send_faculty_digest(recipients: Iterable[str]) -> bool:
    subject = "Weekly Faculty Digest"
    body = "Here are this week’s highlights for faculty."
    return _send(subject, recipients, body)
