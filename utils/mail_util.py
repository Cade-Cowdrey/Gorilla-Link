import os
from flask_mail import Message
from flask import current_app, render_template
from extensions import mail


# -------------------------------------------------
# ✉️ GENERIC EMAIL SENDER
# -------------------------------------------------
def send_email(subject, recipients, html_body, text_body=None):
    """
    Core email utility for PittState-Connect.
    Sends both HTML and plain text emails via Flask-Mail.
    """
    if not recipients:
        current_app.logger.warning("No recipients specified for email.")
        return

    msg = Message(
        subject=f"📣 {subject} | PittState-Connect",
        recipients=recipients,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.edu"),
    )

    msg.html = html_body
    msg.body = text_body or "View this message in HTML format."

    try:
        mail.send(msg)
        current_app.logger.info(f"✅ Email sent to {recipients}")
    except Exception as e:
        current_app.logger.error(f"❌ Failed to send email: {e}")


# -------------------------------------------------
# 📨 WELCOME / CONFIRMATION EMAIL
# -------------------------------------------------
def send_welcome_email(user):
    """Sends PSU-branded welcome / verification email."""
    html_body = render_template("emails/welcome.html", user=user)
    text_body = f"""
Welcome to PittState-Connect, {user.name}!

You're now part of the official PSU networking community — where Gorillas help Gorillas.
Visit your dashboard: {os.getenv('APP_URL', 'https://pittstateconnect.onrender.com')}
"""
    send_email("Welcome to PittState-Connect!", [user.email], html_body, text_body)


# -------------------------------------------------
# 🔐 PASSWORD RESET EMAIL
# -------------------------------------------------
def send_password_reset_email(user, token):
    """Sends PSU-branded password reset email with secure link."""
    reset_url = f"{os.getenv('APP_URL', 'https://pittstateconnect.onrender.com')}/reset-password/{token}"
    html_body = render_template("emails/password_reset.html", user=user, reset_url=reset_url)
    text_body = f"Reset your password by visiting: {reset_url}"
    send_email("Password Reset Request", [user.email], html_body, text_body)


# -------------------------------------------------
# 🧾 ADMIN ANNOUNCEMENT EMAIL
# -------------------------------------------------
def send_admin_announcement(subject, message, recipients):
    """Sends admin-level announcement to multiple users."""
    html_body = render_template("emails/announcement.html", message=message)
    text_body = message
    send_email(subject, recipients, html_body, text_body)


# -------------------------------------------------
# 🗓️ EVENT REMINDER EMAIL
# -------------------------------------------------
def send_event_reminder(user, event):
    """Sends upcoming event reminder email."""
    html_body = render_template("emails/event_reminder.html", user=user, event=event)
    text_body = f"Reminder: {event.title} at {event.location} on {event.start_date.strftime('%b %d, %Y')}."
    send_email(f"Event Reminder: {event.title}", [user.email], html_body, text_body)


# -------------------------------------------------
# 📬 DAILY DIGEST (OPTIONAL)
# -------------------------------------------------
def send_daily_digest(user, posts, events):
    """Sends PSU-branded daily digest email summarizing new posts and events."""
    html_body = render_template("emails/digest.html", user=user, posts=posts, events=events)
    text_body = f"View today's PittState-Connect digest at {os.getenv('APP_URL', 'https://pittstateconnect.onrender.com')}"
    send_email("Your PittState-Connect Daily Digest", [user.email], html_body, text_body)
