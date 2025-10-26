# extensions.py
# Shared extensions for PittState-Connect (production-ready)

from __future__ import annotations
import os, redis
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from flask_cors import CORS
from loguru import logger


# --------------------------------------------------------------------
# 🧩 Database
# --------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()


# --------------------------------------------------------------------
# 🧠 Caching + Redis Client
# --------------------------------------------------------------------
# Flask-Caching wrapper for Redis; redis_client is direct low-level access

cache = Cache(config={
    "CACHE_TYPE": os.getenv("CACHE_TYPE", "RedisCache"),
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "psu_",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL", os.getenv("REDIS_TLS_URL", "redis://localhost:6379/0")),
})

redis_client = None
try:
    redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if redis_url:
        redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Connected to Redis successfully.")
    else:
        logger.warning("⚠️ No REDIS_URL configured; redis_client=None")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None


# --------------------------------------------------------------------
# 📬 Email (SendGrid or SMTP)
# --------------------------------------------------------------------
mail = Mail()
mail_settings = {
    "MAIL_SERVER": os.getenv("MAIL_SERVER", "smtp.sendgrid.net"),
    "MAIL_PORT": int(os.getenv("MAIL_PORT", 587)),
    "MAIL_USE_TLS": True,
    "MAIL_USERNAME": os.getenv("SENDGRID_USERNAME", "apikey"),
    "MAIL_PASSWORD": os.getenv("SENDGRID_API_KEY"),
    "MAIL_DEFAULT_SENDER": os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com"),
}
mail_configured = all(mail_settings.values())
if not mail_configured:
    logger.warning("⚠️ Incomplete mail configuration. Check SENDGRID_API_KEY or MAIL_* vars.")


# --------------------------------------------------------------------
# 🔒 Security, Auth, and CORS
# --------------------------------------------------------------------
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"
login_manager.login_message_category = "info"
CORS = CORS  # exported for app_pro


# --------------------------------------------------------------------
# 🕒 APScheduler
# --------------------------------------------------------------------
scheduler = APScheduler()
scheduler.api_enabled = False


# --------------------------------------------------------------------
# 🔧 Initialization helper (optional)
# --------------------------------------------------------------------
def init_extensions(app):
    """Initialize all extensions within app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)
    logger.info("✅ All extensions initialized for PittState-Connect.")
