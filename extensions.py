"""
PittState-Connect | Application Extensions
Handles DB, Cache, Redis, Mail, Scheduler, Limiter, CSRF, and Analytics hooks.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from loguru import logger
from redis import Redis

# Optional rate limiting
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    Limiter = None
    get_remote_address = None

# ======================================================
# 🔧 Core Extension Instances
# ======================================================
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cache = Cache()
cors = CORS()
scheduler = APScheduler()
csrf = CSRFProtect()

redis_client = None
limiter = None

# ======================================================
# 🧠 Extension Initialization Function
# ======================================================
def init_extensions(app):
    global redis_client, limiter

    logger.info("🧩 extensions.py loaded successfully with production configuration.")

    # ------------------------------------------------------
    # Database
    # ------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    # ------------------------------------------------------
    # Mail
    # ------------------------------------------------------
    mail.init_app(app)

    # ------------------------------------------------------
    # Login Manager
    # ------------------------------------------------------
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # ------------------------------------------------------
    # Cache
    # ------------------------------------------------------
    cache.init_app(app)

    # ------------------------------------------------------
    # CSRF Protection
    # ------------------------------------------------------
    csrf.init_app(app)

    # ------------------------------------------------------
    # CORS
    # ------------------------------------------------------
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    # ------------------------------------------------------
    # Redis
    # ------------------------------------------------------
    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None

    # ------------------------------------------------------
    # Rate Limiter
    # ------------------------------------------------------
    if Limiter:
        try:
            limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=app.config.get("REDIS_URL"),
                default_limits=["200 per hour"],
            )
            limiter.init_app(app)
            logger.info("✅ Limiter initialized successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Limiter initialization failed: {e}")
    else:
        logger.warning("⚠️ Flask-Limiter not installed; skipping limiter setup.")

    # ------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------
    try:
        scheduler.init_app(app)
        schedule_nightly_jobs()
        scheduler.start()
        logger.info("✅ Scheduler initialized successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler setup failed: {e}")

# ======================================================
# 🌙 Nightly Jobs (2 AM CST)
# ======================================================
def schedule_nightly_jobs():
    """Register PSU nightly maintenance and analytics jobs."""
    from datetime import datetime

    def nightly_maintenance():
        logger.info(f"🌙 Nightly maintenance running at {datetime.now()}")
        try:
            if redis_client:
                redis_client.set("last_maintenance_run", str(datetime.now()))
        except Exception as e:
            logger.error(f"Nightly job error: {e}")

    if scheduler.get_job("nightly_maintenance"):
        scheduler.remove_job("nightly_maintenance")

    scheduler.add_job(
        id="nightly_maintenance",
        func=nightly_maintenance,
        trigger="cron",
        hour=2,
        minute=0,
        timezone="America/Chicago",
    )
    logger.info("✅ Nightly job scheduled successfully (2 AM CST).")
