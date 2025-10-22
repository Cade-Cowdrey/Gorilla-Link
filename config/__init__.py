# ============================================================
# FILE: config/__init__.py
# ============================================================

import os
from datetime import timedelta


class Config:
    """Base Flask configuration for PittState-Connect."""

    # Core Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-change-me")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database connection
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings (SendGrid or SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.com"
    )

    # Session and cookie configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Uploads & file limits
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Optional AI/Smart features
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_HELPER_ENABLED = bool(OPENAI_API_KEY)

    # Deployment context
    SERVER_NAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", None)
    PREFERRED_URL_SCHEME = "https"

    # Branding & UI
    APP_NAME = "PittState-Connect"
    UNIVERSITY_NAME = "Pittsburg State University"
    THEME_COLOR_PRIMARY = "#A6192E"  # PSU crimson
    THEME_COLOR_SECONDARY = "#FFB81C"  # PSU gold
