"""Mail utilities for PittState-Connect: handles PSU-branded digest + notifications."""

from flask_mail import Message
from flask import current_app, render_template
from extensions import mail
from datetime import datetime


# ---------- Generic Send Helper ----------
def send_email(subject: str, recipients: list[str], template: str, **kwargs):
    """Generic reusable email sender with PSU branding."""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@pittstate-connect.edu"),
        )
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        current_app.logger.info(f"✅ Sent email '{subject}' -> {recipients}")
    except Exception as e:
        current_app.logger.warning(f"⚠️ Email send failed or skipped: {e}")


# ---------- Digest Senders (Blueprint Imports Depend on These) ----------
def send_weekly_digest_students():
    """Stub for student digest — safe placeholder for production boot."""
    current_app.logger.info("📬 Sending weekly student digest (stub executed successfully).")


def send_weekly_digest_alumni():
    """Stub for alumni digest — safe placeholder for production boot."""
    current_app.logger.info("📬 Sending weekly alumni digest (stub executed successfully).")


def send_faculty_digest():
    """Stub for faculty digest — safe placeholder for production boot."""
    current_app.logger.info("📬 Sending weekly faculty digest (stub executed successfully).")
