# -----------------------------------------------------
# utils/mail_util.py
# PSU-Branded Email Utility (for Digests, Confirmations, etc.)
# -----------------------------------------------------

import os
from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from extensions import mail


# -----------------------------------------------------
# Helper — Send in Background Thread
# -----------------------------------------------------
def _send_async_email(app, msg):
    """Send mail asynchronously (Render-safe)."""
    with app.app_context():
        mail.send(msg)


# -----------------------------------------------------
# General Email Sender
# -----------------------------------------------------
def send_email(subject, recipients, template_name, context=None, plain_name=None, sender=None):
    """
    Sends a PSU-branded email using both plain text and HTML versions.

    Args:
        subject (str): Subject of the email
        recipients (list): List of recipient email addresses
        template_name (str): Path to HTML Jinja2 template (inside templates/emails/)
        plain_name (str): Optional plain-text fallback template
        context (dict): Context variables for rendering (optional)
        sender (str): Sender email (optional override)
    """
    app = current_app._get_current_object()
    context = context or {}

    try:
        sender_email = sender or os.getenv("MAIL_DEFAULT_SENDER", app.config.get("MAIL_USERNAME"))
        msg = Message(subject, recipients=recipients, sender=sender_email)

        # Render templates
        html_body = render_template(f"emails/{template_name}", **context)
        msg.html = html_body

        if plain_name:
            msg.body = render_template(f"emails/plain/{plain_name}", **context)
        else:
            msg.body = "View this message in an HTML-compatible email client."

        # Send asynchronously
        Thread(target=_send_async_email, args=(app, msg)).start()
        app.logger.info(f"📧 Sent '{subject}' email to {recipients}")

    except Exception as e:
        app.logger.error(f"⚠️ Failed to send email: {e}")


# -----------------------------------------------------
# PSU-Branded Digest Email
# -----------------------------------------------------
def send_weekly_digest_students(students):
    """
    Sends the PSU Weekly Digest to all student users.
    """
    app = current_app._get_current_object()
    try:
        with app.app_context():
            for student in students:
                context = {
                    "user": student,
                    "university": "Pittsburg State University",
                    "brand_color": "#DAA520",
                    "base_url": os.getenv("BASE_URL", "https://pittstate-connect.onrender.com"),
                }

                send_email(
                    subject="🎓 Weekly Gorilla Digest — Stay Connected!",
                    recipients=[student.email],
                    template_name="digests/digest_weekly.html",
                    plain_name="digest_weekly.txt",
                    context=context,
                )

            app.logger.info(f"✅ Sent weekly digest to {len(students)} students.")
    except Exception as e:
        app.logger.error(f"⚠️ Failed sending weekly digest: {e}")


# -----------------------------------------------------
# PSU Email Confirmation / Verification
# -----------------------------------------------------
def send_confirmation_email(user_email, token):
    """Sends PSU-branded email confirmation."""
    confirm_url = f"{os.getenv('BASE_URL', 'https://pittstate-connect.onrender.com')}/auth/confirm/{token}"

    send_email(
        subject="PittState-Connect | Confirm Your Email",
        recipients=[user_email],
        template_name="digests/confirmation_email.html",
        plain_name="confirmation_email.txt",
        context={"confirm_url": confirm_url},
    )


# -----------------------------------------------------
# PSU Notification Email
# -----------------------------------------------------
def send_notification_email(user_email, title, message, link=None):
    """Send an event or notification email (PSU branded)."""
    send_email(
        subject=f"PittState-Connect | {title}",
        recipients=[user_email],
        template_name="digests/notification_email.html",
        plain_name="notification_email.txt",
        context={"message": message, "link": link},
    )


# -----------------------------------------------------
# PSU Admin Announcement Email
# -----------------------------------------------------
def send_admin_announcement(recipients, subject, message):
    """Send an announcement to all or select users."""
    for r in recipients:
        send_email(
            subject=f"📣 {subject} — PittState-Connect",
            recipients=[r],
            template_name="digests/admin_announcement.html",
            plain_name="admin_announcement.txt",
            context={"message": message},
        )
