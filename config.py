# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Central Configuration Module (Production + Local)
# ---------------------------------------------------------
import os
from datetime import timedelta


class Config:
    """Base configuration shared across environments."""

    # -----------------------------------------------------
    # Core Flask Settings
    # -----------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///local_dev.db"
    )

    # -----------------------------------------------------
    # Mail Settings
    # -----------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@pittstateconnect.edu"
    )

    # -----------------------------------------------------
    # Redis / Caching
    # -----------------------------------------------------
    REDIS_URL = os.getenv("REDIS_URL")

    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
        CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes
    else:
        CACHE_TYPE = "SimpleCache"
        CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # -----------------------------------------------------
    # Flask-Limiter (Rate Limiting)
    # -----------------------------------------------------
    RATELIMIT_STORAGE_URL = REDIS_URL or "memory://"
    RATELIMIT_DEFAULT = "1000 per hour"

    # -----------------------------------------------------
    # Security / Sessions
    # -----------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # -----------------------------------------------------
    # Scheduler (for digests, cleanup, etc.)
    # -----------------------------------------------------
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"

    # -----------------------------------------------------
    # Branding / Metadata
    # -----------------------------------------------------
    APP_NAME = "PittState-Connect"
    ORGANIZATION = "Pittsburg State University"
    SUPPORT_EMAIL = "support@pittstateconnect.edu"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Local development configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_ECHO = True
    CACHE_TYPE = "SimpleCache"


# ---------------------------------------------------------
# Helper function
# ---------------------------------------------------------
def get_config():
    """Returns the correct config class based on environment."""
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        return DevelopmentConfig
    return ProductionConfig
