# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Email Utility Functions (Flask-Mail)
# ---------------------------------------------------------
from flask import current_app, render_template
from flask_mail import Message
from extensions import mail
import os


# ---------------------------------------------------------
# 🔧 Helper: Send a generic email
# ---------------------------------------------------------
def send_email(subject, recipients, html_body, text_body=None):
    msg = Message(
        subject,
        recipients=recipients,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER", "no-reply@pittstateconnect.edu"),
    )
    msg.html = html_body
    if text_body:
        msg.body = text_body
    try:
        mail.send(msg)
        current_app.logger.info(f"📧 Email sent to {recipients}: {subject}")
    except Exception as e:
        current_app.logger.error(f"❌ Email failed: {e}")


# ---------------------------------------------------------
# ✉️ Verification Email
# ---------------------------------------------------------
def send_verification_email(user, token):
    verify_url = f"{os.getenv('BASE_URL', 'https://pittstateconnect.onrender.com')}/verify/{token}"
    html_body = render_template("emails/account_verification.html", user=user, verify_url=verify_url)
    text_body = render_template("emails/plain/account_verification.txt", user=user, verify_url=verify_url)
    send_email("Verify your PittState-Connect account", [user.email], html_body, text_body)


# ---------------------------------------------------------
# 🔑 Password Reset Email
# ---------------------------------------------------------
def send_password_reset_email(user, token):
    reset_url = f"{os.getenv('BASE_URL', 'https://pittstateconnect.onrender.com')}/reset-password/{token}"
    html_body = render_template("emails/password_reset.html", user=user, reset_url=reset_url)
    text_body = render_template("emails/plain/password_reset.txt", user=user, reset_url=reset_url)
    send_email("Reset your PittState-Connect password", [user.email], html_body, text_body)


# ---------------------------------------------------------
# 🎉 Welcome Email (after verification)
# ---------------------------------------------------------
def send_welcome_email(user):
    html_body = render_template("emails/welcome.html", user=user)
    text_body = render_template("emails/plain/welcome.txt", user=user)
    send_email("Welcome to PittState-Connect!", [user.email], html_body, text_body)


# ---------------------------------------------------------
# 📰 Weekly Digest Emails (Alumni + General)
# ---------------------------------------------------------
def send_weekly_digest_alumni(user, posts, events):
    """Placeholder for alumni digest system — prevents import errors."""
    html_body = render_template("emails/alumni_digest.html", user=user, posts=posts, events=events)
    text_body = render_template("emails/plain/alumni_digest.txt", user=user, posts=posts, events=events)
    send_email("Your PittState Alumni Weekly Digest", [user.email], html_body, text_body)


def send_weekly_digest_general(user, posts, events):
    """General student digest placeholder."""
    html_body = render_template("emails/general_digest.html", user=user, posts=posts, events=events)
    text_body = render_template("emails/plain/general_digest.txt", user=user, posts=posts, events=events)
    send_email("Your PittState Weekly Digest", [user.email], html_body, text_body)
