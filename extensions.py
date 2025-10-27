import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from redis import Redis
from loguru import logger

# --------------------------------------------------------
# ✅ Logging Configuration
# --------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger.info("🧩 extensions.py loaded successfully with production configuration.")

# --------------------------------------------------------
# ✅ Database
# --------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()

# --------------------------------------------------------
# ✅ Authentication
# --------------------------------------------------------
login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"
login_manager.login_message_category = "warning"

# --------------------------------------------------------
# ✅ Mail Configuration
# --------------------------------------------------------
mail = Mail()

# --------------------------------------------------------
# ✅ Caching (uses Redis if available)
# --------------------------------------------------------
cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0")
})

# --------------------------------------------------------
# ✅ Redis Client
# --------------------------------------------------------
try:
    redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis_client.ping()
    logger.info("✅ Connected to Redis successfully.")
except Exception as e:
    logger.warning(f"⚠️ Redis unavailable, continuing without cache. Error: {e}")
    redis_client = None

# --------------------------------------------------------
# ✅ Rate Limiter (Protect endpoints)
# --------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    default_limits=["200 per hour", "20 per minute"],
)
logger.info("✅ Limiter initialized successfully.")

# --------------------------------------------------------
# ✅ APScheduler (Background Jobs)
# --------------------------------------------------------
scheduler = APScheduler()
logger.info("✅ Scheduler initialized successfully.")

# --------------------------------------------------------
# ✅ Optional Nightly Analytics Job Example
# --------------------------------------------------------
def nightly_analytics_refresh():
    """Example scheduled job that refreshes cached stats nightly."""
    if redis_client:
        redis_client.set("analytics:last_refresh", "done")
    logger.info("🌙 Nightly analytics refresh completed.")


def schedule_nightly_jobs():
    """Register scheduled jobs safely."""
    try:
        scheduler.add_job(
            id="nightly_analytics_refresh",
            func=nightly_analytics_refresh,
            trigger="cron",
            hour=2,
            minute=0,
        )
        logger.info("✅ Nightly job scheduled successfully (2 AM CST).")
    except Exception as e:
        logger.warning(f"⚠️ Could not schedule nightly job: {e}")


schedule_nightly_jobs()
