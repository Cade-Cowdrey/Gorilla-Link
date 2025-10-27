"""
extensions.py
Centralized Flask extension initialization for PittState-Connect (Production Build)
Handles SQLAlchemy, Migrate, Mail, Cache (Redis), Login, CSRF, Scheduler, and AI integration.
"""

import os
import logging
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from redis import Redis

# ============================================================
# Core Flask Extensions
# ============================================================

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()

# ============================================================
# Redis Client Setup
# ============================================================

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

try:
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Connected to Redis successfully.")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None


# ============================================================
# Login Manager Configuration
# ============================================================

login_manager.login_view = "core_bp.login"
login_manager.login_message_category = "info"


# ============================================================
# AI Assistant / OpenAI Setup (Optional)
# ============================================================

def init_ai_helper():
    """Initialize AI helper if OpenAI key is configured."""
    import openai

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        openai.api_key = openai_key
        logger.info("🤖 OpenAI Assistant initialized.")
        return True
    else:
        logger.warning("⚠️ OpenAI API key not found — AI assistant disabled.")
        return False


# ============================================================
# Utility: Init all extensions for an app context
# ============================================================

def init_extensions(app):
    """Attach all extensions to a Flask app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": "RedisCache", "CACHE_REDIS_URL": redis_url})
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)

    # Start scheduler (safe to skip if already running)
    try:
        scheduler.start()
    except Exception as e:
        logger.warning(f"⚠️ Scheduler already running or failed to start: {e}")

    # Optional AI helper initialization
    init_ai_helper()

    logger.info("🔧 Flask extensions initialized successfully.")
    return app


# ============================================================
# Database Connection Health Check
# ============================================================

def test_database_connection(app):
    """Quickly verify DB connectivity on startup."""
    try:
        with app.app_context():
            db.session.execute("SELECT 1")
        logger.info("✅ Database connection verified.")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


# ============================================================
# Mail Health Check
# ============================================================

def test_mail(app):
    """Ensure mail settings are complete."""
    mail_user = app.config.get("MAIL_USERNAME")
    mail_pass = app.config.get("MAIL_PASSWORD")
    if not (mail_user and mail_pass):
        logger.warning("⚠️ Incomplete mail configuration. Check MAIL_USERNAME / MAIL_PASSWORD.")
        return False
    logger.info("📨 Mail configuration verified.")
    return True


# ============================================================
# Analytics / Scheduled Jobs Hooks
# ============================================================

def register_scheduled_jobs(app):
    """Register nightly analytics and faculty index jobs."""
    try:
        from blueprints.analytics.tasks import refresh_insight_cache
        scheduler.add_job(
            id="nightly_analytics_refresh",
            func=refresh_insight_cache,
            trigger="cron",
            hour=3
        )
        logger.info("📊 Nightly analytics job scheduled.")
    except Exception as e:
        logger.warning(f"⚠️ Analytics job not scheduled: {e}")

    try:
        from blueprints.faculty.tasks import rebuild_search_index
        scheduler.add_job(
            id="faculty_reindex",
            func=rebuild_search_index,
            trigger="interval",
            hours=24
        )
        logger.info("👨‍🏫 Faculty reindex job scheduled.")
    except Exception as e:
        logger.warning(f"⚠️ Faculty reindex job not scheduled: {e}")


# ============================================================
# Extension Summary
# ============================================================

logger.info("🧩 extensions.py loaded successfully with production configuration.")
