# /config/dev.py
import os

class DevConfig:
    """Development configuration for PittState-Connect."""
    DEBUG = True
    TESTING = False

    # Database (local Postgres or SQLite fallback)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///dev.db"
    ).replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key & session
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SESSION_TYPE = "filesystem"

    # Email (local test)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "dev@pittstateconnect.local")

    # Redis caching
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Flask-Talisman security
    TALISMAN_FORCE_HTTPS = False
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": "* data:",
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
    }

    # OpenAI API for dev AI helper
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"

    # File storage
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

    # Scheduler
    SCHEDULER_API_ENABLED = True

    # Logging
    LOG_LEVEL = "DEBUG"

    # Analytics mock mode
    ANALYTICS_SIMULATION = True
