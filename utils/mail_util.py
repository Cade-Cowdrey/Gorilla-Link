"""Utility functions for sending PSU-branded email digests and notifications."""

from flask_mail import Message
from flask import current_app, render_template
from extensions import mail
from datetime import datetime


# ---------- Core PSU Mail Helper ----------
def send_email(subject: str, recipients: list[str], template: str, **kwargs):
    """Generic PSU email sender (safe fail)."""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@pittstate-connect.edu"),
        )
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        current_app.logger.info(f"✅ Sent email: {subject} -> {recipients}")
        return True
    except Exception as e:
        current_app.logger.warning(f"⚠️ Email sending skipped or failed: {e}")
        return False


# ---------- PSU Digest Emails ----------
def send_weekly_digest_students():
    """Send weekly digest emails to all active PSU students."""
    try:
        from models import User, Role
        from extensions import db

        student_role = db.session.query(Role).filter_by(name="Student").first()
        if not student_role:
            current_app.logger.warning("No 'Student' role found.")
            return

        students = db.session.query(User).filter_by(role_id=student_role.id, is_active=True).all()
        for student in students:
            send_email(
                subject="Your Weekly PittState-Connect Digest 🦍",
                recipients=[student.email],
                template="emails/digests/student_digest.html",
                user=student,
                week=datetime.utcnow().isocalendar().week,
            )
        current_app.logger.info(f"📨 Sent student digests: {len(students)} recipients")
    except Exception as e:
        current_app.logger.error(f"Error sending student digests: {e}")


def send_weekly_digest_alumni():
    """Send weekly digest emails to all registered PSU alumni."""
    try:
        from models import User, Role
        from extensions import db

        alumni_role = db.session.query(Role).filter_by(name="Alumni").first()
        if not alumni_role:
            current_app.logger.warning("No 'Alumni' role found.")
            return

        alumni = db.session.query(User).filter_by(role_id=alumni_role.id, is_active=True).all()
        for alum in alumni:
            send_email(
                subject="Alumni Weekly Digest — Stay Connected 🦍",
                recipients=[alum.email],
                template="emails/digests/alumni_digest.html",
                user=alum,
                week=datetime.utcnow().isocalendar().week,
            )
        current_app.logger.info(f"📨 Sent alumni digests: {len(alumni)} recipients")
    except Exception as e:
        current_app.logger.error(f"Error sending alumni digests: {e}")


def send_faculty_digest():
    """Send faculty-specific summary of campus/student highlights."""
    try:
        from models import User, Role
        from extensions import db

        faculty_role = db.session.query(Role).filter_by(name="Faculty").first()
        if not faculty_role:
            current_app.logger.warning("No 'Faculty' role found.")
            return

        faculty_members = db.session.query(User).filter_by(role_id=faculty_role.id, is_active=True).all()
        for faculty in faculty_members:
            send_email(
                subject="Faculty Digest — PSU Highlights & Student News 🦍",
                recipients=[faculty.email],
                template="emails/digests/faculty_digest.html",
                user=faculty,
                week=datetime.utcnow().isocalendar().week,
            )
        current_app.logger.info(f"📨 Sent faculty digests: {len(faculty_members)} recipients")
    except Exception as e:
        current_app.logger.error(f"Error sending faculty digests: {e}")
