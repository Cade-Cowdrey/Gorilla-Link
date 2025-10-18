# ---------------------------------------------
#  utils/mail_util.py — complete, resilient
# ---------------------------------------------
import os
from flask_mail import Mail, Message
from flask import render_template, render_template_string, current_app

mail = Mail()

def init_mail(app):
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "smtp.gmail.com"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", 587)))
    app.config.setdefault("MAIL_USE_TLS", True)
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com"))
    mail.init_app(app)

def _render_email(template, context):
    # Prefer a real template if available; otherwise render a fallback PSU-branded string.
    try:
        return render_template(template, **(context or {}))
    except Exception:
        html = """
        <div style="font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial">
          <h2 style="color:#73000A;margin:0 0 8px;">PittState-Connect</h2>
          <div style="border-top:2px solid #FFD700;margin:10px 0 18px;"></div>
          {% for k,v in context.items() %}
            <p><strong>{{k}}</strong>: {{v}}</p>
          {% endfor %}
          <p style="color:#666;">This is a fallback email. Add a template at {{ template }} to customize.</p>
        </div>
        """
        return render_template_string(html, template=template, context=(context or {}))

def send_email(recipient, subject, html_template, context=None):
    with current_app.app_context():
        msg = Message(subject, recipients=[recipient])
        msg.html = _render_email(html_template, context)
        try:
            mail.send(msg)
            current_app.logger.info(f"✅ Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            current_app.logger.error(f"❌ Email send failed to {recipient}: {e}")
            return False

# --- Common flows
def send_verification_email(user_email, confirm_url):
    return send_email(
        recipient=user_email,
        subject="Confirm Your PittState-Connect Account",
        html_template="emails/confirm_email.html",
        context={"confirm_url": confirm_url}
    )

def send_reset_email(user_email, reset_url):
    return send_email(
        recipient=user_email,
        subject="PittState-Connect Password Reset",
        html_template="emails/reset_password_email.html",
        context={"reset_url": reset_url}
    )

def send_verified_success_email(user_email):
    return send_email(
        recipient=user_email,
        subject="Your PittState-Connect Account is Verified 🎉",
        html_template="emails/verified_success_email.html",
        context={}
    )

# --- Digest helpers referenced by blueprints & admin
def build_weekly_digest_data(audience="students"):
    """
    Return a dict of data that can be rendered in digest emails.
    Extend to query DB for top posts, events, jobs, etc.
    """
    # Minimal example; replace with real queries.
    return {
        "audience": audience,
        "highlights": [
            {"title": "New Events Posted", "count": 5},
            {"title": "Top Stories", "count": 3},
            {"title": "New Opportunities", "count": 4},
        ]
    }

def send_weekly_digest_email(audience="students"):
    data = build_weekly_digest_data(audience=audience)
    return send_email(
        recipient=os.getenv("DIGEST_TO", "digest-demo@pittstateconnect.com"),
        subject=f"PittState-Connect Weekly Digest — {audience.title()}",
        html_template="emails/weekly_digest.html",
        context=data
    )

def send_weekly_digest_students():
    return send_weekly_digest_email(audience="students")

def send_weekly_digest_alumni():
    return send_weekly_digest_email(audience="alumni")

def send_faculty_digest():
    return send_weekly_digest_email(audience="faculty")
