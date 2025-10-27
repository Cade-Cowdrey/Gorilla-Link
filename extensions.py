import os
import redis
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_caching import Cache
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
scheduler = APScheduler()
login_manager = LoginManager()
csrf = CSRFProtect()
redis_client = None

def init_extensions(app):
    """Attach extensions to the Flask app with production-grade options."""
    global redis_client

    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("🗄️  Database + Migrations initialized")

    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"
    logger.info("🔐 LoginManager initialized")

    mail.init_app(app)
    if not (app.config.get("MAIL_USERNAME") or app.config.get("SENDGRID_API_KEY")):
        logger.warning("⚠️ Incomplete mail configuration detected.")
    else:
        logger.info("📧 Mail subsystem ready")

    cache.init_app(app)
    logger.info("⚡ Cache initialized (Flask-Caching)")

    try:
        redis_url = app.config.get("REDIS_URL") or os.getenv("REDIS_URL")
        if redis_url:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            logger.info("✅ Connected to Redis successfully")
        else:
            logger.warning("⚠️ No REDIS_URL found; Redis features disabled.")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        redis_client = None

    scheduler.init_app(app)
    try:
        scheduler.start()
        logger.info("⏰ APScheduler started successfully")
    except Exception as e:
        logger.warning(f"⚠️ APScheduler skipped: {e}")

    csrf.init_app(app)
    logger.info("🛡️ CSRF protection enabled")

    return app
