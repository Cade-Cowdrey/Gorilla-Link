# extensions.py
# ---------------------------------------------------------------------
# Centralized extension initialization for PittState-Connect
# - SQLAlchemy, Flask-Migrate, Flask-Mail
# - Redis (analytics, cache, scheduler)
# - CORS, CSRF, LoginManager
# ---------------------------------------------------------------------

import os
import logging
import redis
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf import CSRFProtect

# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | extensions | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# Flask core extensions
# ---------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()

# ---------------------------------------------------------------------
# Redis configuration (for analytics, caching, schedulers)
# ---------------------------------------------------------------------
def init_redis_client() -> redis.Redis | None:
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=5)
        client.ping()
        logger.info("✅ Connected to Redis successfully.")
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable, continuing without cache: {e}")
        return None

redis_client = init_redis_client()

# ---------------------------------------------------------------------
# Initialization helper for app_pro.py
# ---------------------------------------------------------------------
def init_extensions(app):
    """Initializes all extensions with Flask app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    cors.init_app(app)

    app.logger.info("✅ All extensions initialized successfully.")

    # Optional login defaults
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # Optional Redis availability test
    if redis_client:
        try:
            redis_client.set("psu:test", "ok", ex=10)
            app.logger.info("Redis test write succeeded.")
        except Exception:
            app.logger.warning("Redis test write failed, disabling runtime cache.")
