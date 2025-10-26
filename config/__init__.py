# config/__init__.py
# ---------------------------------------------------------------------
# PittState-Connect Configuration Suite (Production Ready)
# ---------------------------------------------------------------------
# Provides:
#  - Environment-aware configuration classes (Development, Testing, Production)
#  - Secure defaults for Flask, SQLAlchemy, Mail, Redis, and CORS
#  - Integrated Sentry monitoring (optional, auto-disabled if DSN missing)
#  - PSU branding metadata and UI constants
#  - Optional OpenAI / analytics / task scheduler support
#  - Render-safe and local-friendly auto-detection
# ---------------------------------------------------------------------

import os
import logging
from datetime import timedelta

# Optional: Sentry error monitoring
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration(), RedisIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=1.0,
            send_default_pii=True,
            environment=os.getenv("FLASK_ENV", "production").capitalize(),
        )
        logging.info("✅ Sentry monitoring initialized")
    else:
        logging.info("⚠️ Sentry DSN not provided — monitoring disabled")
except ImportError:
    logging.warning("⚠️ Sentry SDK not installed — skipping Sentry integration")
except Exception as e:
    logging.warning(f"⚠️ Sentry initialization error: {e}")


# ---------------------------------------------------------------------
# Core Configuration Base
# ---------------------------------------------------------------------
class Config:
    """Base configuration for all environments."""

    # General
    APP_NAME = "PittState-Connect"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = False
    TESTING = False

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///pittstate_connect.db"
    ).replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Redis / Cache
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.edu")
    MAIL_SUPPRESS_SEND = False

    # Scheduler / Jobs
    SCHEDULER_API_ENABLED = True
    JOBS_REFRESH_INTERVAL = 60  # seconds

    # OpenAI / Smart Assistant
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ASSISTANT_ENABLED = bool(OPENAI_API_KEY)

    # Analytics & Telemetry
    ENABLE_ANALYTICS = True
    ANALYTICS_STORAGE_BACKEND = os.getenv("ANALYTICS_BACKEND", "redis")
    ANALYTICS_CACHE_TTL = 300  # seconds

    # PSU Branding
    PSU_PRIMARY_COLOR = "#DAAA00"  # PSU Gold
    PSU_SECONDARY_COLOR = "#861F41"  # PSU Crimson
    PSU_TAGLINE = "PittState-Connect: Linking Students, Alumni, and Opportunity."
    PSU_LOGO_PATH = "/static/img/psu_logo.svg"

    # Rate Limiting (via Flask-Limiter)
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = REDIS_URL

    # Security Headers
    CSP = {
        "default-src": "'self'",
        "script-src": ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        "style-src": ["'self'", "fonts.googleapis.com", "cdn.jsdelivr.net"],
        "font-src": ["'self'", "fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "cdn.pittstateconnect.edu"],
        "connect-src": ["'self'", "api.openai.com"],
    }

    # Logging
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

    # Audit / Retention
    AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", 30))

    # Feature Flags
    ENABLE_SCHOLARSHIP_HUB = True
    ENABLE_JOB_MATCHING = True
    ENABLE_DONOR_PORTAL = True
    ENABLE_DEPARTMENT_ANALYTICS = True
    ENABLE_AI_RECOMMENDER = True
    ENABLE_PEER_MENTORS = True


# ---------------------------------------------------------------------
# Environment-specific Configs
# ---------------------------------------------------------------------

class DevelopmentConfig(Config):
    """Local Development Settings"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect_dev.db"
    )
    SESSION_COOKIE_SECURE = False
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False
    ENABLE_ANALYTICS = True
    ENV_NAME = "development"


class TestingConfig(Config):
    """CI / Unit Testing Settings"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False
    ENABLE_ANALYTICS = False
    ENV_NAME = "testing"


class ProductionConfig(Config):
    """Production Settings"""
    DEBUG = False
    TESTING = False
    RATELIMIT_ENABLED = True
    SESSION_COOKIE_SECURE = True
    ENV_NAME = "production"

    # Optimize SQLAlchemy
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 15,
        "pool_timeout": 30,
        "pool_pre_ping": True,
    }

    # Enforce HTTPS
    PREFERRED_URL_SCHEME = "https"

    # Background job scheduler frequency
    JOBS_REFRESH_INTERVAL = 300

    # Error reporting
    ERROR_REPORTING_ENABLED = True


# ---------------------------------------------------------------------
# Utility: resolve active config class
# ---------------------------------------------------------------------

def get_config_class() -> str:
    """Return the full import path of the active config class."""
    env = os.getenv("FLASK_ENV", "production").lower()
    if env in ("dev", "development"):
        return "config.DevelopmentConfig"
    elif env in ("test", "testing"):
        return "config.TestingConfig"
    else:
        return "config.ProductionConfig"


# ---------------------------------------------------------------------
# Optional: Global logging config (executed early in app factory)
# ---------------------------------------------------------------------
def setup_logging():
    """Apply unified log formatting across the app."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT,
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.info("✅ PSU Config logging initialized successfully")
