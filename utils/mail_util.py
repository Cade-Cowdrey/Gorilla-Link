import os
from flask_mail import Message
from flask import current_app, render_template
from extensions import mail

# -------------------------------------------------
# ✉️ GENERIC EMAIL SENDER
# -------------------------------------------------
def send_email(subject, recipients, html_body, text_body=None):
    """Core email utility for PittState-Connect."""
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
# 📨 WELCOME / ACCOUNT ACTIVATION EMAIL
# -------------------------------------------------
def send_welcome_email(user):
    """Sends PSU-branded welcome email."""
    html_body = render_template("emails/welcome.html", user=user)
    text_body = render_template("emails/plain/welcome.txt", user=user)
    send_email("Welcome to PittState-Connect!", [user.email], html_body, text_body)


# -------------------------------------------------
# 🧾 VERIFICATION EMAIL (for new users)
# -------------------------------------------------
def send_verification_email(user, token):
    """Sends PSU-branded email verification link."""
    verify_url = f"{os.getenv('APP_URL', 'https://pittstateconnect.onrender.com')}/verify/{token}"
    html_body = render_template("emails/account_verification.html", user=user, verify_url=verify_url)
    text_body = f"Hello {user.name}, please verify your email: {verify_url}"
    send_email("Verify Your PittState-Connect Account", [user.email], html_body, text_body)


# -------------------------------------------------
# 🔐 PASSWORD RESET EMAIL
# -------------------------------------------------
def send_password_reset_email(user, token):
    """Sends PSU-branded password reset email with secure link."""
    reset_url = f"{os.getenv('APP_URL', 'https://pittstateconnect.onrender.com')}/reset-password/{token}"
    html_body = render_template("emails/password_reset.html", user=user, reset_url=reset_url)
    text_body = render_template("emails/plain/password_reset.txt", user=user, reset_url=reset_url)
    send_email("Password Reset Request", [user.email], html_body, text_body)


# -------------------------------------------------
# 🗞️ WEEKLY DIGEST EMAIL (students)
# -------------------------------------------------
def send_weekly_digest_students(users, posts, events):
    """
    Sends a weekly digest email to all active students.
    Placeholder version — safe to import even if unused.
    """
    for user in users:
        html_body = render_template("emails/digest.html", user=user, posts=posts, events=events)
        text_body = render_template("emails/plain/digest.txt", user=user, posts=posts, events=events)
        send_email("Your Weekly Gorilla Digest", [user.email], html_body, text_body)


# -------------------------------------------------
# 🧾 ADMIN ANNOUNCEMENT EMAIL
# -------------------------------------------------
def send_admin_announcement(subject, message, recipients):
    """Sends admin-level announcement to multiple users."""
    html_body = render_template("emails/announcement.html", message=message)
    text_body = render_template("emails/plain/announcement.txt", message=message)
    send_email(subject, recipients, html_body, text_body)


# -------------------------------------------------
# 🗓️ EVENT REMINDER EMAIL
# -------------------------------------------------
def send_event_reminder(user, event):
    """Sends upcoming event reminder email."""
    html_body = render_template("emails/event_reminder.html", user=user, event=event)
    text_body = render_template("emails/plain/event_reminder.txt", user=user, event=event)
    send_email(f"Event Reminder: {event.title}", [user.email], html_body, text_body)


# -------------------------------------------------
# 📬 DAILY DIGEST EMAIL
# -------------------------------------------------
def send_daily_digest(user, posts, events):
    """Sends PSU-branded daily digest email summarizing new posts and events."""
    html_body = render_template("emails/digest.html", user=user, posts=posts, events=events)
    text_body = render_template("emails/plain/digest.txt", user=user, posts=posts, events=events)
    send_email("Your PittState-Connect Daily Digest", [user.email], html_body, text_body)
