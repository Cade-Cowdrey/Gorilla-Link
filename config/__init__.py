"""
config/__init__.py
Production-ready configuration loader for PittState-Connect
Includes Redis, Postgres, Mail, Scheduler, Analytics, and AI helper support.
"""

import os
import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from redis import Redis
import openai


# ======================
# Flask Extensions
# ======================
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
csrf = CSRFProtect()
login_manager = LoginManager()
scheduler = APScheduler()


# ======================
# Helper Functions
# ======================

def init_logger(app: Flask):
    """Initialize rotating file + console logger for production"""
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pittstate_connect.log")

    file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler.setFormatter(formatter)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("📜 Logging initialized successfully.")


def init_openai():
    """Configure OpenAI if API key provided"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai.api_key = api_key
        return True
    return False


# ======================
# App Factory
# ======================

def create_app():
    app = Flask(__name__)

    # ----------------------
    # Load production config
    # ----------------------
    app.config.from_object("config.config_production.ConfigProduction")

    # SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)

    # Mail
    mail.init_app(app)

    # Redis cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache.init_app(app, config={"CACHE_TYPE": "RedisCache", "CACHE_REDIS_URL": redis_url})

    # CSRF protection
    csrf.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "core_bp.login"

    # Scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Initialize optional services
    if init_openai():
        app.logger.info("🤖 OpenAI Assistant connected successfully.")
    else:
        app.logger.warning("⚠️ OpenAI API key not set; AI features disabled.")

    # Analytics / nightly jobs
    try:
        from blueprints.analytics.tasks import refresh_insight_cache
        scheduler.add_job(
            id="nightly_analytics_refresh",
            func=refresh_insight_cache,
            trigger="cron",
            hour=3,
        )
        app.logger.info("📊 Nightly analytics refresh job scheduled.")
    except Exception as e:
        app.logger.warning(f"⚠️ Skipped analytics scheduler setup: {e}")

    # Faculty search index rebuild
    try:
        from blueprints.faculty.tasks import rebuild_search_index
        scheduler.add_job(
            id="faculty_reindex",
            func=rebuild_search_index,
            trigger="interval",
            hours=24,
        )
        app.logger.info("👨‍🏫 Faculty index rebuild job scheduled.")
    except Exception as e:
        app.logger.warning(f"⚠️ Skipped faculty reindex job setup: {e}")

    # Logging setup
    init_logger(app)

    # Redis connection test
    try:
        redis_client = Redis.from_url(redis_url)
        redis_client.ping()
        app.logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        app.logger.warning(f"⚠️ Redis connection failed: {e}")

    # DB connection test
    try:
        with app.app_context():
            db.session.execute("SELECT 1")
        app.logger.info("✅ Connected to Postgres database successfully.")
    except Exception as e:
        app.logger.error(f"❌ Database connection failed: {e}")

    # Final status
    app.logger.info("🚀 PittState-Connect production app initialized successfully.")

    return app


# ======================
# Production Config Class
# ======================

class ConfigProduction:
    """Production configuration for Render deployment"""

    SECRET_KEY = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # Redis / Cache
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"

    # Session / Security
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Misc
    DEBUG = False
    TESTING = False

