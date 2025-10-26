import os
from datetime import timedelta
from dotenv import load_dotenv

# ============================================================
# 🧩 Load environment variables
# ============================================================
load_dotenv()

# ============================================================
# 🌎 Base Config
# ============================================================
class Config:
    # --- Core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-psu-connect-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")

    # ============================================================
    # 🗄️ Database Configuration (PostgreSQL for Render)
    # ============================================================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:password@localhost:5432/pittstate_connect"
    ).replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ============================================================
    # 🧠 Redis & Caching
    # ============================================================
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # ============================================================
    # 📬 Flask-Mail / SendGrid Integration
    # ============================================================
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("SENDGRID_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("SENDGRID_API_KEY", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

    # ============================================================
    # 🔐 Security & Session
    # ============================================================
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # ============================================================
    # 🤖 OpenAI / Smart Match Enhancements
    # ============================================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_SMART_MATCH_ENABLED = os.getenv("AI_SMART_MATCH_ENABLED", "True").lower() in ("true", "1")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_MAX_TOKENS = 1500
    AI_TEMPERATURE = 0.7

    # ============================================================
    # 📊 Analytics, Insights, and Logging
    # ============================================================
    ENABLE_ANALYTICS_DASHBOARD = True
    ANALYTICS_REFRESH_INTERVAL = int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "900"))  # 15 minutes
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ============================================================
    # 📅 APScheduler (Background Jobs)
    # ============================================================
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"
    JOBS = [
        {
            "id": "nightly_cleanup",
            "func": "extensions:nightly_maintenance",
            "trigger": "cron",
            "hour": 3,
        },
        {
            "id": "analytics_refresh",
            "func": "blueprints.analytics.tasks:refresh_insight_cache",
            "trigger": "interval",
            "minutes": 15,
        },
    ]

    # ============================================================
    # 🧾 PSU Branding Defaults (used in emails and UI)
    # ============================================================
    PSU_NAME = "Pittsburg State University"
    PSU_TAGLINE = "Experience the Power of the Gorilla Spirit"
    PSU_LOGO_PATH = "/static/img/psu-logo.png"
    PSU_COLORS = {
        "primary": "#DA291C",  # Gorilla Crimson
        "secondary": "#FFC72C",  # PSU Gold
        "accent": "#000000",
    }

    # ============================================================
    # 🧰 File Uploads / Cloud Buckets
    # ============================================================
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/")
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx"}
    USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "False").lower() in ("true", "1")
    CLOUD_BUCKET_NAME = os.getenv("CLOUD_BUCKET_NAME", "psu-connect-bucket")

    # ============================================================
    # 🔔 Notifications & Email Digests
    # ============================================================
    ENABLE_EMAIL_DIGESTS = True
    DAILY_DIGEST_HOUR = 8  # 8 AM
    DIGEST_TEMPLATE = "emails/digests/daily_digest.html"

    # ============================================================
    # 🧩 Accessibility & Compliance
    # ============================================================
    ACCESSIBILITY_MODE = True
    COLOR_CONTRAST_MIN_RATIO = 4.5
    ENABLE_KEYBOARD_NAVIGATION = True
    GDPR_COMPLIANT = True


# ============================================================
# 🔰 Environment-Specific Configs
# ============================================================
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    CACHE_TYPE = "simple"


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CACHE_TYPE = "null"


# ============================================================
# 🔍 Configuration Loader
# ============================================================
def get_config():
    """Return the correct config class depending on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        return DevelopmentConfig
    elif env == "testing":
        return TestingConfig
    else:
        return ProductionConfig
