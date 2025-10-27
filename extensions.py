"""
extensions.py
--------------------------------------------------
Centralized Flask extension initialization for
PittState-Connect production environment.
--------------------------------------------------
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from redis import Redis
from flask_cors import CORS
from loguru import logger

# Flask extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
mail = Mail()
scheduler = APScheduler()
login_manager = LoginManager()
redis_client = None


def init_extensions(app):
    """Initialize all Flask extensions with proper config."""
    global redis_client

    # --- Database ---
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("✅ Database & Migrations initialized.")

    # --- Cache / Redis ---
    try:
        redis_client = Redis.from_url(app.config.get("CACHE_REDIS_URL"))
        redis_client.ping()
        cache.init_app(app)
        logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        redis_client = None
        logger.warning(f"⚠️ Redis connection failed: {e}")

    # --- Mail ---
    mail.init_app(app)
    logger.info("📧 Mail service configured (SendGrid/Flask-Mail).")

    # --- Scheduler ---
    scheduler.init_app(app)
    scheduler.start()
    logger.info("🕒 APScheduler started successfully.")

    # --- CORS ---
    CORS(app, resources={r"/*": {"origins": "*"}})
    logger.info("🌐 CORS enabled for all routes.")

    # --- Login ---
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    logger.info("🔐 Login manager initialized.")


def get_redis_client():
    """Expose redis_client safely."""
    return redis_client
