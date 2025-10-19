import os
from flask import current_app, render_template
from flask_mail import Message
from extensions import mail


# -------------------------------------------------------------
# 🏫 PSU-Branded Mail Utility for PittState-Connect
# -------------------------------------------------------------

def send_email(subject, recipients, html_body, sender=None):
    """Universal helper to send PSU-branded emails with Flask-Mail."""
    try:
        if not mail:
            raise RuntimeError("Flask-Mail not initialized yet.")
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            sender=sender or os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstate-connect.com"),
        )
        msg.html = html_body
        mail.send(msg)
        current_app.logger.info(f"📧 Sent email '{subject}' to {recipients}")
    except Exception as e:
        current_app.logger.warning(f"⚠️ Email send failed ({subject}): {e}")


# -------------------------------------------------------------
# 🔐 1. Verification Email
# -------------------------------------------------------------
def send_verification_email(user_email, token=None):
    """Send account verification email to new users."""
    verification_link = f"{os.getenv('BASE_URL', 'https://pittstate-connect.onrender.com')}/verify/{token or 'demo-token'}"
    html = render_template(
        "emails/verification_email.html",
        verification_link=verification_link,
        user_email=user_email,
    )
    send_email("Verify Your PittState-Connect Account", user_email, html)


# -------------------------------------------------------------
# 🔑 2. Password Reset Email
# -------------------------------------------------------------
def send_password_reset_email(user_email, reset_token):
    """Send password reset link."""
    reset_link = f"{os.getenv('BASE_URL', 'https://pittstate-connect.onrender.com')}/reset/{reset_token}"
    html = render_template(
        "emails/reset_password_email.html",
        reset_link=reset_link,
        user_email=user_email,
    )
    send_email("Reset Your PittState-Connect Password", user_email, html)


# -------------------------------------------------------------
# 📰 3. Weekly Digest Email (Alumni + Students)
# -------------------------------------------------------------
def send_weekly_digest_alumni(alumni_email_list=None):
    """Send PSU-branded weekly digest summary to alumni."""
    if not alumni_email_list:
        alumni_email_list = ["demo_alumni@pittstate.edu"]

    html = render_template(
        "emails/jungle_digest_email.html",
        digest_title="This Week in Gorilla Nation 🦍",
        summary_points=[
            "🎓 New mentorships formed between alumni and students",
            "🏢 Career board: 12 new internship listings",
            "📅 Campus events this week at PSU",
        ],
        footer_note="Stay connected. Stay a Gorilla.",
    )
    send_email("Your Weekly PittState-Connect Digest", alumni_email_list, html)


# -------------------------------------------------------------
# ✉️ 4. General-purpose Mailer for Admins
# -------------------------------------------------------------
def send_admin_announcement(subject, body, recipients):
    """Allow admin announcements with PSU header/footer."""
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #fafafa;">
        <h2 style="color:#990000;">{subject}</h2>
        <p style="font-size:16px; color:#333;">{body}</p>
        <hr style="border:1px solid #d4af37;">
        <footer style="font-size:14px; color:#666;">
            Sent via <strong>PittState-Connect</strong><br>
            Pittsburg State University 🦍
        </footer>
    </div>
    """
    send_email(subject, recipients, html)


# -------------------------------------------------------------
# 🧩 5. Safe Fallback Stubs
# -------------------------------------------------------------
def safe_stub_log(name):
    """Logs that a stub mailer was called instead of real function."""
    current_app.logger.info(f"[MAIL STUB] '{name}' called safely — no action taken.")


# If any imports in blueprints expect these names, ensure they exist:
def send_verification_email_stub(user_email: str):
    safe_stub_log("send_verification_email_stub")


def send_weekly_digest_alumni_stub():
    safe_stub_log("send_weekly_digest_alumni_stub")


# For backward compatibility with older imports:
if "send_verification_email" not in globals():
    send_verification_email = send_verification_email_stub

if "send_weekly_digest_alumni" not in globals():
    send_weekly_digest_alumni = send_weekly_digest_alumni_stub


# -------------------------------------------------------------
# ✅ Optional test route (can remove in production)
# -------------------------------------------------------------
def test_mail_system():
    """Quick test utility for debugging Render mail integration."""
    demo_html = "<p>This is a <strong>PittState-Connect</strong> test email.</p>"
    send_email("PittState-Connect Test Email", "you@pittstate.edu", demo_html)
    return "✅ Mail system tested (check logs or inbox)."
