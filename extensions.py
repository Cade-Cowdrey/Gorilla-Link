"""
extensions.py
--------------------------------
Centralized extension initialization for PittState-Connect.
Includes Redis caching, CORS, CSRF, APScheduler, mail, login,
and PSU security & analytics integration.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_caching import Cache
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from flask_cors import CORS
from loguru import logger
import os

# ============================================================
# 🧩 Core Flask Extensions
# ============================================================
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
scheduler = APScheduler()
csrf = CSRFProtect()
login_manager = LoginManager()

# ============================================================
# 🌎 Global Security & Utility Settings
# ============================================================
def init_app(app):
    """Initialize all extensions with the Flask app context."""
    # --- Logging Setup ---
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    logger.remove()
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="14 days",
        level=log_level,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    logger.info(f"🔒 Loguru initialized with level: {log_level}")

    # --- Database ---
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("✅ Database & migrations initialized.")

    # --- Mail ---
    mail.init_app(app)
    logger.info("📧 Mail service initialized (SendGrid/SMTP).")

    # --- Cache (Redis) ---
    try:
        cache.init_app(app)
        with app.app_context():
            cache.set("cache_test_key", "success", timeout=10)
        logger.info("⚡ Redis cache connected and verified.")
    except Exception as e:
        logger.warning(f"⚠️ Redis cache fallback to simple cache: {e}")
        app.config["CACHE_TYPE"] = "simple"
        cache.init_app(app)

    # --- CSRF Protection ---
    csrf.init_app(app)
    logger.info("🛡️ CSRF protection enabled for all routes.")

    # --- Cross-Origin Resource Sharing (CORS) ---
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        expose_headers=["Content-Type", "Authorization", "X-Requested-With"],
        allow_headers=["Content-Type", "Authorization", "X-CSRFToken"],
    )
    logger.info(f"🌐 CORS enabled for origins: {allowed_origins}")

    # --- Scheduler (APScheduler) ---
    try:
        scheduler.api_enabled = True
        scheduler.init_app(app)
        scheduler.start()
        logger.info("🕒 Scheduler started successfully.")
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {e}")

    # --- Login Manager ---
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"
    logger.info("👤 Flask-Login initialized.")

    # --- Custom PSU Branding ---
    app.jinja_env.globals.update(
        PSU_NAME=app.config.get("PSU_NAME", "Pittsburg State University"),
        PSU_TAGLINE=app.config.get("PSU_TAGLINE", "Experience the Power of the Gorilla Spirit"),
        PSU_COLORS=app.config.get("PSU_COLORS", {}),
        PSU_LOGO_PATH=app.config.get("PSU_LOGO_PATH", "/static/img/psu-logo.png"),
    )
    logger.info("🎨 PSU branding context injected into templates.")

    # --- Health Check Cache Warmup ---
    @app.before_first_request
    def warm_cache():
        cache.set("health_check", "ok", timeout=600)
        logger.info("🔥 Health cache prewarmed on startup.")

    logger.success("✅ All extensions initialized successfully.")
    return app


# ============================================================
# 🧼 Nightly Maintenance Job (Auto-Cleanup + Analytics)
# ============================================================
def nightly_maintenance():
    """Nightly job for PSU analytics, cleanup, and notifications."""
    from datetime import datetime
    from models import User, Scholarship

    logger.info(f"🌙 Running nightly maintenance at {datetime.utcnow()}")

    try:
        # Example: Update cached analytics
        user_count = User.query.count()
        scholarship_count = Scholarship.query.count()
        cache.set("metrics:user_count", user_count, timeout=86400)
        cache.set("metrics:scholarship_count", scholarship_count, timeout=86400)

        # Optional: Clear expired cache or tokens
        cache.delete("health_check")

        logger.success(f"✅ Nightly metrics updated — Users: {user_count}, Scholarships: {scholarship_count}")
    except Exception as e:
        logger.error(f"❌ Nightly maintenance error: {e}")
