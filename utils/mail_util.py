"""
PittState-Connect | Mail Utility
Handles all outgoing email operations across the platform.
Uses Redis-based queueing for async delivery by worker.py.
"""

import json
from loguru import logger
from flask_mail import Message
from flask import current_app
from extensions import mail, redis_client


# ======================================================
# ✉️ QUEUE-BASED EMAIL SENDER
# ======================================================
def queue_email(subject, recipients, body, html=None):
    """
    Push an email task to Redis queue for async sending by worker.py.
    """
    try:
        if not redis_client:
            logger.warning("⚠️ Redis not connected — sending email immediately (sync fallback).")
            send_email_immediate(subject, recipients, body, html)
            return

        email_task = {
            "subject": subject,
            "recipients": recipients,
            "body": body,
            "html": html,
        }
        redis_client.rpush("email_queue", json.dumps(email_task))
        logger.info(f"📬 Queued email for delivery to {recipients}")
    except Exception as e:
        logger.error(f"❌ Failed to queue email: {e}")
        # Fallback to direct send
        send_email_immediate(subject, recipients, body, html)


# ======================================================
# 🚀 IMMEDIATE EMAIL FALLBACK
# ======================================================
def send_email_immediate(subject, recipients, body, html=None):
    """
    Send an email directly using Flask-Mail.
    Used only if Redis is unavailable or queue fails.
    """
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )
        mail.send(msg)
        logger.info(f"📧 Sent email immediately to {recipients}")
    except Exception as e:
        logger.error(f"💥 Email send failure: {e}")


# ======================================================
# 🧠 SMART TEMPLATED EMAILS (OPTIONAL PSU THEMING)
# ======================================================
def send_templated_email(recipient, template_name, context):
    """
    Sends a PSU-branded HTML email using Jinja2 templates under templates/emails/.
    Example usage:
        send_templated_email(
            recipient='student@gus.pittstate.edu',
            template_name='welcome.html',
            context={'name': 'Connor', 'portal_url': 'https://pittstateconnect.com'}
        )
    """
    from flask import render_template

    try:
        html_body = render_template(f"emails/{template_name}", **context)
        subject = context.get("subject", "PittState-Connect Notification")
        queue_email(subject, [recipient], body="See HTML version.", html=html_body)
        logger.info(f"🦍 PSU-branded email '{template_name}' queued for {recipient}")
    except Exception as e:
        logger.error(f"❌ Failed to render/send templated email {template_name}: {e}")
