# config/settings.py
# PittState-Connect Configuration Set (production-ready)

import os
from datetime import timedelta


# ==========================================================
#  Base Configuration (shared across all environments)
# ==========================================================
class BaseConfig:
    # --- Core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect.db"
    ).replace("postgres://", "postgresql://")

    # --- Caching / Redis ---
    CACHE_TYPE = os.getenv("CACHE_TYPE", "RedisCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_KEY_PREFIX = "psu_"
    CACHE_REDIS_URL = os.getenv("REDIS_URL") or os.getenv(
        "REDIS_TLS_URL", "redis://localhost:6379/0"
    )

    # --- Flask-Mail / SendGrid ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("SENDGRID_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("SENDGRID_API_KEY", "")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com"
    )

    # --- Scheduler ---
    SCHEDULER_API_ENABLED = False
    SCHEDULER_TIMEZONE = os.getenv("TZ", "America/Chicago")

    # --- Security / Cookies ---
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    WTF_CSRF_ENABLED = True

    # --- Logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # --- CORS ---
    CORS_RESOURCES = {r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}}

    # --- OpenAI API ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- PSU Branding ---
    APP_NAME = "PittState-Connect"
    UNIVERSITY_NAME = "Pittsburg State University"
    PRIMARY_COLOR = "#BA0C2F"  # PSU Crimson
    SECONDARY_COLOR = "#FFD100"  # PSU Gold
    SUPPORT_EMAIL = "support@pittstateconnect.com"

    # --- Optional Analytics Settings ---
    ANALYTICS_REFRESH_HOUR = 2  # nightly at 2 AM
    FACULTY_REINDEX_HOUR = 3
    ENABLE_SMART_MATCH = True
    ENABLE_AI_RECOMMENDER = True
    ENABLE_DEADLINE_TRACKER = True
    ENABLE_DONOR_PORTAL = True
    ENABLE_FINANCIAL_DASHBOARDS = True


# ==========================================================
#  Production Configuration (Render default)
# ==========================================================
class ProductionConfig(BaseConfig):
    ENV = "production"
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = "https"
    CACHE_DEFAULT_TIMEOUT = 600
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
    }
    MAIL_SUPPRESS_SEND = False


# ==========================================================
#  Development Configuration (local dev)
# ==========================================================
class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DEV_DATABASE_URL", "sqlite:///pittstate_connect_dev.db"
    )
    CACHE_TYPE = "SimpleCache"
    MAIL_SUPPRESS_SEND = True
    CORS_RESOURCES = {r"/*": {"origins": "*"}}


# ==========================================================
#  Testing Configuration (unit tests / CI)
# ==========================================================
class TestingConfig(BaseConfig):
    ENV = "testing"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CACHE_TYPE = "NullCache"
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
