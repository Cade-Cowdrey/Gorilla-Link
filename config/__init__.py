"""
config/__init__.py
--------------------------------------------------
PittState-Connect Unified Configuration Loader
Combines database, mail, cache, and security configs.
--------------------------------------------------
"""

import os
from dotenv import load_dotenv
from loguru import logger
from config.mail_config import MailConfig

load_dotenv()  # Load .env or .env.production automatically


class BaseConfig:
    """Core config shared across environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "pittstate-super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Caching / Redis
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Flask-Mail and SendGrid
    MAIL_SERVER = MailConfig.MAIL_SERVER
    MAIL_PORT = MailConfig.MAIL_PORT
    MAIL_USE_TLS = MailConfig.MAIL_USE_TLS
    MAIL_USERNAME = MailConfig.MAIL_USERNAME
    MAIL_PASSWORD = MailConfig.MAIL_PASSWORD
    MAIL_DEFAULT_SENDER = MailConfig.MAIL_DEFAULT_SENDER

    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"

    # Security and Logging
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class ProductionConfig(BaseConfig):
    """Production-specific overrides."""

    ENV = "production"
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    """Development mode."""

    ENV = "development"
    DEBUG = True


def get_config():
    """Return appropriate config class."""
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        logger.info("🧩 Using DevelopmentConfig")
        return DevelopmentConfig
    logger.info("🚀 Using ProductionConfig")
    return ProductionConfig
