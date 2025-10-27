"""
PittState-Connect | Development Configuration
For local testing and safe feature development.
Uses SQLite or a local Postgres instance, console logging, and verbose error output.
"""

import os

class config_development:
    # Flask Core
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-psu-2025")

    # Database (local SQLite by default, or Postgres if specified)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect_dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis (use local unless overridden)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Email
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "dev_email@example.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "password123")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "PittState Connect (DEV) <noreply@pittstate.edu>"
    )

    # Rate Limiting / Cache
    RATELIMIT_DEFAULT = "100 per minute"
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # Analytics / AI / Feature Flags
    ENABLE_ANALYTICS = True
    ENABLE_AI_ASSISTANT = True
    MAINTENANCE_MODE = False

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

    # Misc
    ENV = "development"
