# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Mail Utility — PSU Branded Email System
# ---------------------------------------------------------
from flask_mail import Message
from flask import render_template, current_app
from extensions import mail
from models import User, Department
import traceback

# ---------------------------------------------------------
# Core Send Function
# ---------------------------------------------------------
def send_email(subject, recipients, template_name, **context):
    """Send an email using a Jinja2 HTML template."""
    try:
        msg = Message(
            subject,
            recipients=recipients,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com"),
        )
        msg.html = render_template(f"emails/{template_name}.html", **context)
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email send failed: {e}")
        traceback.print_exc()
        return False

# ---------------------------------------------------------
# Weekly Faculty Digest (Used by digests blueprint)
# ---------------------------------------------------------
def send_faculty_digest():
    """Send weekly digest to faculty and department heads."""
    try:
        faculty_users = User.query.filter(User.role == "faculty").all()
        departments = Department.query.all()

        for faculty in faculty_users:
            send_email(
                subject="📊 Weekly Faculty Digest | PittState-Connect",
                recipients=[faculty.email],
                template_name="emails/jungle_digest_email",
                user=faculty,
                departments=departments,
            )

        return True
    except Exception as e:
        current_app.logger.error(f"Faculty digest failed: {e}")
        traceback.print_exc()
        return False

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
def ping_mail():
    return "✅ Mail utility ready."
