import os
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_wtf import CSRFProtect
from loguru import logger
from redis import Redis

# ============================================================
# 🔰 Logging setup
# ============================================================
logger.remove()
logger.add(
    sink=lambda msg: print(msg, flush=True),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="INFO"
)

# ============================================================
# ⚙️ Flask Extensions
# ============================================================
db = SQLAlchemy()
cache = Cache()
mail = Mail()
migrate = Migrate()
scheduler = APScheduler()
login_manager = LoginManager()
csrf = CSRFProtect()

# ============================================================
# 🧠 Redis Configuration Helper
# ============================================================
def init_redis_connection():
    """Initialize a Redis client for caching, analytics, and messaging."""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = Redis.from_url(redis_url)
        client.ping()
        logger.info("✅ Connected to Redis successfully.")
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        return None


redis_client = init_redis_connection()

# ============================================================
# 🧩 App Initialization Function
# ============================================================
def init_app(app):
    """Initialize all extensions safely in a production environment."""
    # --- Database ---
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("✅ Database and migration initialized.")

    # --- CSRF Protection ---
    csrf.init_app(app)
    logger.info("✅ CSRF protection enabled.")

    # --- Caching (Redis or Simple) ---
    cache_type = "redis" if redis_client else "simple"
    cache_config = {
        "CACHE_TYPE": cache_type,
        "CACHE_REDIS_URL": os.getenv("REDIS_URL"),
        "CACHE_DEFAULT_TIMEOUT": 300
    }
    cache.init_app(app, config=cache_config)
    logger.info(f"✅ Cache initialized ({cache_type}).")

    # --- Flask Mail ---
    mail.init_app(app)
    logger.info("✅ Flask-Mail initialized.")

    # --- Scheduler ---
    scheduler.init_app(app)
    scheduler.start()
    logger.info("✅ APScheduler initialized and running.")

    # --- Login Manager ---
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"
    logger.info("✅ Flask-Login initialized.")

    # --- Add security headers to every response ---
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    logger.info("✅ Security headers enabled.")

    # --- Final confirmation ---
    logger.success("🚀 All extensions initialized successfully in production mode.")

# ============================================================
# 💡 Example Scheduled Task
# ============================================================
@scheduler.task("cron", id="nightly_maintenance", hour=3)
def nightly_maintenance():
    """
    Example nightly job that could:
    - Clean old logs
    - Update job/analytics tables
    - Send donor report digests
    """
    from datetime import datetime
    now = datetime.utcnow()
    logger.info(f"🌙 Running nightly maintenance @ {now}")
    if redis_client:
        redis_client.set("last_maintenance", now.isoformat())
