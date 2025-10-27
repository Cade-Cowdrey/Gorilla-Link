"""
Mail utilities: enqueue-first design with safe fallbacks.

Enhancements:
- Enqueue by default (worker handles SendGrid/Flask-Mail routing)
- Optional direct-send for local/dev (MAIL_SYNC_SEND=true)
- Jinja2 HTML rendering helper with minimal base template support
- Input validation + defensive logging
- Redis fallback creation if extensions.redis_client is missing
"""

import os
import json
from typing import Optional, Dict

from loguru import logger

# --- Redis helper -------------------------------------------------------------
def _get_redis():
    try:
        from extensions import redis_client as shared_client  # type: ignore
        if shared_client:
            return shared_client
    except Exception:
        pass
    REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not REDIS_URL:
        return None
    try:
        import redis  # type: ignore
        return redis.from_url(REDIS_URL, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("mail_util: Redis unavailable: {}", e)
        return None


redis_client = _get_redis()
MAIL_QUEUE_KEY = os.getenv("MAIL_QUEUE_KEY", "queue:mail")

# --- Optional direct send (dev) ----------------------------------------------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
MAIL_SYNC_SEND = os.getenv("MAIL_SYNC_SEND", "").lower() in {"1", "true", "yes", "on"}

_sendgrid_client = None
if SENDGRID_API_KEY and MAIL_SYNC_SEND:
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import From, To, Subject, HtmlContent, Mail as SGMail
        _sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        logger.error("mail_util: SendGrid init failed: {}", e)
        _sendgrid_client = None


def render_html(subject: str, body_html: str) -> str:
    """Tiny wrapper to ensure a basic HTML envelope."""
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{subject}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;line-height:1.5;color:#111">
  {body_html}
  <hr style="margin-top:24px;border:none;border-top:1px solid #eee">
  <p style="font-size:12px;color:#666">PittState-Connect • Automated message</p>
</body>
</html>"""


def _send_direct(to_email: str, subject: str, html: str, sender: str) -> bool:
    """Dev-only direct send via SendGrid (bypasses the queue)."""
    if not _sendgrid_client:
        return False
    try:
        msg = SGMail(from_email=From(sender), to_emails=To(to_email),
                     subject=Subject(subject), html_content=HtmlContent(html))
        resp = _sendgrid_client.send(msg)
        ok = 200 <= int(resp.status_code) < 300
        if not ok:
            logger.warning("mail_util: direct SendGrid non-2xx: {}", resp.status_code)
        return ok
    except Exception as e:
        logger.error("mail_util: direct send failed: {}", e)
        return False


def enqueue_email(
    to_email: str,
    subject: str,
    html_body: str,
    sender: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Enqueue an email for worker.py to deliver. Returns True on success.
    In dev, set MAIL_SYNC_SEND=true to send synchronously via SendGrid.
    """
    if not to_email or "@" not in to_email:
        logger.warning("enqueue_email: invalid recipient: {}", to_email)
        return False

    sender = sender or os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")
    html = render_html(subject, html_body)

    # Synchronous path (dev/testing)
    if MAIL_SYNC_SEND:
        ok = _send_direct(to_email, subject, html, sender)
        if ok:
            logger.info("mail_util: direct-sent -> {}", to_email)
        return ok

    # Enqueue path (prod)
    if not redis_client:
        logger.warning("enqueue_email: Redis not configured; cannot enqueue")
        return False

    payload = {"to": to_email, "subject": subject, "html": html, "sender": sender}
    if headers:
        payload["headers"] = headers

    try:
        redis_client.lpush(MAIL_QUEUE_KEY, json.dumps(payload))
        logger.info("mail_util: enqueued -> {}", to_email)
        return True
    except Exception as e:
        logger.error("enqueue_email failed: {}", e)
        return False
