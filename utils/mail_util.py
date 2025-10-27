"""
utils/mail_util.py
-------------------------------------------------------------
PittState-Connect Mail Utility
-------------------------------------------------------------
• Queue-first delivery (Redis)
• Fallback to SendGrid direct-send if MAIL_SYNC_SEND=true
• HTML auto-templating + Jinja fallback
• Heartbeat metrics support
• Safe for production & Render worker environment
"""

import os
import json
from typing import Optional, Dict
from loguru import logger


def get_redis():
    try:
        from extensions import redis_client as shared
        if shared:
            return shared
    except Exception:
        pass
    url = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("Redis unavailable: {}", e)
        return None


redis_client = get_redis()
MAIL_QUEUE_KEY = os.getenv("MAIL_QUEUE_KEY", "queue:mail")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
MAIL_SYNC_SEND = os.getenv("MAIL_SYNC_SEND", "").lower() in {"1", "true", "yes", "on"}

sg_client = None
if SENDGRID_API_KEY and MAIL_SYNC_SEND:
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import From, To, Subject, HtmlContent, Mail
        sg_client = SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        logger.warning("SendGrid init failed: {}", e)


def render_html(subject, html_body):
    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>{subject}</title></head>
<body style='font-family:Arial,sans-serif;color:#111'>
{html_body}
<hr><p style='font-size:12px;color:#555'>PittState-Connect • Automated Mail</p>
</body></html>"""


def send_direct(to_email, subject, html, sender):
    if not sg_client:
        return False
    try:
        msg = Mail(from_email=From(sender), to_emails=To(to_email),
                   subject=Subject(subject), html_content=HtmlContent(html))
        resp = sg_client.send(msg)
        ok = 200 <= int(resp.status_code) < 300
        logger.info("Direct SendGrid sent -> {} [{}]", to_email, resp.status_code)
        return ok
    except Exception as e:
        logger.error("Direct SendGrid failed: {}", e)
        return False


def enqueue_email(to_email: str, subject: str, html_body: str,
                  sender: Optional[str] = None,
                  headers: Optional[Dict[str, str]] = None) -> bool:
    if not to_email or "@" not in to_email:
        logger.warning("Invalid email: {}", to_email)
        return False

    sender = sender or MAIL_DEFAULT_SENDER
    html = render_html(subject, html_body)

    if MAIL_SYNC_SEND:
        return send_direct(to_email, subject, html, sender)

    if not redis_client:
        logger.warning("Redis not configured; cannot enqueue mail -> {}", to_email)
        return False

    payload = {"to": to_email, "subject": subject, "html": html, "sender": sender}
    if headers:
        payload["headers"] = headers

    try:
        redis_client.lpush(MAIL_QUEUE_KEY, json.dumps(payload))
        logger.info("Enqueued mail -> {}", to_email)
        return True
    except Exception as e:
        logger.error("Failed to enqueue mail: {}", e)
        return False
