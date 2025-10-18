# utils.py
# ===========================================
# Gorilla-Link Utility Toolkit
# ===========================================
import json
import secrets
import string
import logging
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from extensions import mail, cache

# -------------------------------------------------
# 🔒 SECURITY HELPERS
# -------------------------------------------------
def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token (for admin, cron, etc.)."""
    return secrets.token_urlsafe(length)

def generate_random_key(length: int = 16) -> str:
    """Generate a readable random key for demo IDs or API keys."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# -------------------------------------------------
# 🕒 TIME UTILITIES
# -------------------------------------------------
def current_central_time() -> datetime:
    """Return current time in Central Time (CST/CDT)."""
    from pytz import timezone
    tz = timezone("America/Chicago")
    return datetime.now(tz)

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %I:%M %p") -> str:
    """Format a datetime safely."""
    return dt.strftime(fmt) if dt else ""

def days_ago(days: int) -> datetime:
    """Return datetime object N days ago."""
    return datetime.utcnow() - timedelta(days=days)

# -------------------------------------------------
# 📨 EMAIL UTILITIES
# -------------------------------------------------
def send_email(subject: str, recipients: list[str], body: str, html: str = None) -> bool:
    """Send an email safely using Flask-Mail."""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        )
        mail.send(msg)
        current_app.logger.info(f"✅ Email sent to {recipients}")
        return True
    except Exception as e:
        current_app.logger.error(f"❌ Email send failed: {e}")
        return False

# -------------------------------------------------
# 💾 JSON / CACHE HELPERS
# -------------------------------------------------
def safe_json_dumps(data: dict, indent: int = 2) -> str:
    """Safely serialize JSON."""
    try:
        return json.dumps(data, indent=indent, default=str)
    except Exception as e:
        current_app.logger.warning(f"JSON dump failed: {e}")
        return "{}"

def cached(key: str, ttl: int = 300):
    """Decorator for caching view results for short durations."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            cached_val = cache.get(key)
            if cached_val:
                current_app.logger.debug(f"🧠 Cache hit: {key}")
                return cached_val
            result = fn(*args, **kwargs)
            cache.set(key, result, timeout=ttl)
            current_app.logger.debug(f"💾 Cache set: {key}")
            return result
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

# -------------------------------------------------
# 📊 ANALYTICS HELPERS
# -------------------------------------------------
def calculate_growth(current: int, previous: int) -> str:
    """Return percentage growth string."""
    try:
        if previous == 0:
            return "∞%"
        diff = ((current - previous) / previous) * 100
        return f"{diff:+.1f}%"
    except Exception:
        return "0.0%"

# -------------------------------------------------
# 🧰 GENERAL UTILITIES
# -------------------------------------------------
def log_event(message: str, level: str = "info"):
    """Quick logging shortcut for Render logs."""
    logger = logging.getLogger("GorillaLink")
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)

def is_admin_token(token: str) -> bool:
    """Validate if a token matches admin token in env."""
    return token == current_app.config.get("ADMIN_TOKEN")
