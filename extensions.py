"""
PittState-Connect | Global Extensions Loader
Handles initialization of Flask extensions for Production, Development, and Testing.

Includes:
- SQLAlchemy & Migrate
- Redis client & Caching
- Flask-Login, CSRF, Mail
- Rate Limiter (Flask-Limiter)
- APScheduler (Nightly jobs)
- PSU-branded structured logging
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
import redis
from loguru import logger
from datetime import datetime

# ======================================================
# 🧱 CORE INITIALIZATIONS
# ======================================================
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
cache = Cache()
limiter = None
scheduler = APScheduler()
redis_client = None


# ======================================================
# 🧠 LOGGER SETUP
# ======================================================
logger.remove()
logger.add(
    sink=lambda msg: print(msg, flush=True),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
)
logger.info("🧩 extensions.py loaded successfully with production configuration.")


# ======================================================
# 🚀 INITIALIZATION FUNCTION
# ======================================================
def init_extensions(app):
    """Initialize all app extensions using the active configuration."""

    # --- Database & Migrate ---
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Redis ---
    global redis_client
    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.StrictRedis.from_url(redis_url)
        redis_client.ping()
        logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

    # --- Cache ---
    cache.init_app(app)

    # --- Mail ---
    mail.init_app(app)

    # --- CSRF Protection ---
    csrf.init_app(app)

    # --- Login Manager ---
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # --- Rate Limiter ---
    global limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri=redis_url,
        strategy="moving-window",
    )
    logger.info("✅ Limiter initialized successfully.")

    # --- Scheduler ---
    scheduler.api_enabled = False
    scheduler.init_app(app)
    scheduler.start()
    logger.info("✅ Scheduler initialized successfully.")

    # --- Register Nightly Jobs ---
    schedule_nightly_jobs()

    # --- Optional Feature Toggles ---
    if app.config.get("ENABLE_ANALYTICS"):
        logger.info("📊 Analytics engine enabled.")
    if app.config.get("ENABLE_AI_ASSISTANT"):
        logger.info("🤖 AI Assistant module enabled.")
    if app.config.get("MAINTENANCE_MODE"):
        logger.warning("🚧 App currently in maintenance mode.")

    logger.info("🦍 All PittState-Connect extensions initialized successfully.")


# ======================================================
# 🌙 NIGHTLY JOBS
# ======================================================
def nightly_data_refresh():
    """Example nightly job — refresh analytics, expire cache, sync AI models."""
    try:
        logger.info("🌙 Running nightly job: Analytics + Cache Refresh")
        if redis_client:
            redis_client.flushdb()
            logger.info("♻️ Redis cache cleared successfully.")
        # Placeholder for future enhancements:
        # from utils.analytics import refresh_university_metrics
        # refresh_university_metrics()
        logger.info(f"✅ Nightly maintenance completed at {datetime.utcnow()}")
    except Exception as e:
        logger.error(f"❌ Nightly job failed: {e}")


def schedule_nightly_jobs():
    """Schedules nightly jobs (runs every day at 2 AM CST)."""
    try:
        scheduler.add_job(
            id="nightly_refresh",
            func=nightly_data_refresh,
            trigger="cron",
            hour=2,
            minute=0,
            timezone="US/Central",
        )
        logger.info("✅ Nightly job scheduled successfully (2 AM CST).")
    except Exception as e:
        logger.error(f"❌ Failed to schedule nightly job: {e}")


# ======================================================
# 🧩 EXPORTS
# ======================================================
__all__ = [
    "db",
    "migrate",
    "login_manager",
    "mail",
    "csrf",
    "cache",
    "limiter",
    "scheduler",
    "redis_client",
    "init_extensions",
]
