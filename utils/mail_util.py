import os
from flask import current_app
from flask_mail import Message
from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
from extensions import mail, redis_client


# =========================================================
# 🦍 PittState-Connect | Unified Mail Utility
# =========================================================

def send_email(subject, recipients, html_body=None, text_body=None, sender=None, attachments=None):
    """
    Sends an email via SendGrid if available, else Flask-Mail.
    Supports both HTML + plaintext fallbacks.
    """
    sender = sender or os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")
    api_key = os.getenv("SENDGRID_API_KEY")

    try:
        # ==========================================
        # 🔹 Option A: SendGrid (preferred)
        # ==========================================
        if api_key:
            sg = SendGridAPIClient(api_key)

            # Construct email
            message = Mail(
                from_email=Email(sender, "PittState-Connect"),
                to_emails=recipients,
                subject=subject,
                html_content=html_body or "",
            )

            # Add plaintext fallback
            if text_body:
                message.add_content(Content("text/plain", text_body))

            # Optional attachments
            if attachments:
                for att in attachments:
                    message.add_attachment(att)

            response = sg.send(message)

            logger.info(f"📧 SendGrid email sent → {recipients} | Status: {response.status_code}")
            _log_email_event(subject, recipients, "sendgrid", response.status_code)
            return True

        # ==========================================
        # 🔹 Option B: Flask-Mail Fallback
        # ==========================================
        else:
            msg = Message(subject, recipients=recipients, sender=sender)
            if html_body:
                msg.html = html_body
            if text_body:
                msg.body = text_body

            # Add attachments (tuple: (filename, mimetype, data))
            if attachments:
                for filename, mimetype, data in attachments:
                    msg.attach(filename, mimetype, data)

            mail.send(msg)
            logger.info(f"📬 SMTP email sent → {recipients}")
            _log_email_event(subject, recipients, "flask_mail", 200)
            return True

    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        _log_email_event(subject, recipients, "error", 500)
        return False


# =========================================================
# 🧠 Utility for Logging Email Events to Redis
# =========================================================
def _log_email_event(subject, recipients, provider, status):
    """
    Stores a short email log in Redis for analytics dashboard or later audit.
    """
    try:
        if not redis_client:
            logger.warning("⚠️ Redis unavailable, skipping email log.")
            return

        event = {
            "subject": subject,
            "recipients": recipients,
            "provider": provider,
            "status": status,
        }
        redis_client.lpush("email_logs", str(event))
        redis_client.ltrim("email_logs", 0, 999)  # Keep only last 1000 entries
    except Exception as e:
        logger.warning(f"⚠️ Could not log email event: {e}")


# =========================================================
# 🕒 Optional Scheduled Reports / Nightly Summary
# =========================================================
def send_nightly_summary():
    """
    Sends a nightly summary to admins showing number of emails sent via SendGrid/SMTP.
    (Optional APScheduler job)
    """
    try:
        if not redis_client:
            logger.warning("⚠️ Redis unavailable for nightly summary.")
            return

        logs = redis_client.lrange("email_logs", 0, -1)
        total = len(logs)
        sg_count = sum("sendgrid" in str(l) for l in logs)
        smtp_count = sum("flask_mail" in str(l) for l in logs)

        html = f"""
        <h3 style="color:#9E1B32;">📊 PittState-Connect Email Summary</h3>
        <p>Total sent: <strong>{total}</strong></p>
        <p>SendGrid: {sg_count} | SMTP: {smtp_count}</p>
        """

        send_email(
            subject="PittState-Connect Nightly Email Report",
            recipients=[os.getenv("ADMIN_EMAIL", "admin@pittstateconnect.com")],
            html_body=html,
            text_body=f"Total sent: {total}\nSendGrid: {sg_count}\nSMTP: {smtp_count}",
        )

        logger.info("🌙 Nightly email summary sent successfully.")
    except Exception as e:
        logger.error(f"❌ Failed nightly summary: {e}")
