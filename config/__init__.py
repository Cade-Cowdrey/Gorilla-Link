# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Configuration Manager — get_config() helper
# ---------------------------------------------------------
import os


class BaseConfig:
    """Base configuration shared by all environments."""

    # Flask Core
    SECRET_KEY = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate_connect.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

    # Cache (Redis on Render)
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # APScheduler
    SCHEDULER_API_ENABLED = True

    # Rate Limiting
    RATELIMIT_DEFAULT = "200/hour"
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Branding
    SITE_NAME = "PittState-Connect"
    SITE_TAGLINE = "Connecting Gorillas for Life"


class ProductionConfig(BaseConfig):
    """Production config for Render."""
    DEBUG = False
    TESTING = False


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""
    DEBUG = True
    TESTING = True


class TestingConfig(BaseConfig):
    """Used for unit testing."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


# ---------------------------------------------------------
# Factory Function
# ---------------------------------------------------------
def get_config():
    """Return the appropriate configuration class."""
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        return DevelopmentConfig
    elif env == "testing":
        return TestingConfig
    else:
        return ProductionConfig
