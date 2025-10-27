# config/config_production.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class ConfigProduction:
    """Production configuration for PittState-Connect (Render Deployment)."""

    # === Core Flask ===
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-psu-key")
    FLASK_ENV = "production"
    DEBUG = False
    TESTING = False
    SERVER_NAME = None  # Let Render handle domain routing

    # === Database ===
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30
    }

    # === Redis + Cache ===
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes cache
    CACHE_KEY_PREFIX = "pittstate_connect_"

    # === Security (CSRF, Session, Cookies) ===
    SESSION_TYPE = "redis"
    SESSION_REDIS = REDIS_URL
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True

    # === Flask-Mail (SendGrid or SMTP) ===
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "apikey")  # SendGrid default
    MAIL_PASSWORD = os.getenv("SENDGRID_API_KEY", "")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "PittState-Connect <noreply@pittstate.edu>"
    )

    # === OpenAI / Smart Assistant ===
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ASSISTANT_ENABLED = True
    AI_ASSISTANT_MODEL = "gpt-4o-mini"
    AI_ASSISTANT_SYSTEM_PROMPT = (
        "You are the official PittState-Connect AI assistant. "
        "Provide helpful, PSU-branded, student-friendly guidance."
    )

    # === Scheduler (Nightly jobs) ===
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"

    # === Analytics / Insights ===
    ANALYTICS_CACHE_TTL = 1800  # 30 minutes
    ENABLE_ANALYTICS_DASHBOARD = True

    # === File uploads ===
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

    # === Logging / Monitoring ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"

    # === Feature Flags (Optional Enhancements) ===
    ENABLE_SMART_SCHOLARSHIP_MATCH = True
    ENABLE_DONOR_PORTAL = True
    ENABLE_AI_ESSAY_HELPER = True
    ENABLE_ANALYTICS_REPORTING = True
    ENABLE_PEER_MENTOR_SYSTEM = True
    ENABLE_FACULTY_RECOMMENDATIONS = True
    ENABLE_EMPLOYER_ENGAGEMENT = True
    ENABLE_LEADERBOARDS = True
    ENABLE_FINANCIAL_LITERACY_HUB = True
    ENABLE_TIMELINE_TRACKER = True

    # === Branding ===
    UNIVERSITY_NAME = "Pittsburg State University"
    APP_NAME = "PittState-Connect"
    PRIMARY_COLOR = "#990000"
    SECONDARY_COLOR = "#FFCC00"
    TAGLINE = "Connecting Gorillas — Students, Alumni, and Employers"

    # === Optional External APIs ===
    GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "")
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    ENABLE_SENTRY = bool(SENTRY_DSN)

    # === CORS ===
    CORS_ALLOW_ORIGINS = ["https://pittstate-connect.onrender.com"]
    CORS_SUPPORTS_CREDENTIALS = True

    # === Timezone ===
    TIMEZONE = "America/Chicago"
