# ============================================================
# FILE: config/config_dev.py
# Local development configuration for PittState-Connect
# ============================================================

import os
from datetime import timedelta


class DevConfig:
    """Local development configuration."""

    # Flask basics
    SECRET_KEY = "dev-secret-key"
    FLASK_ENV = "development"
    DEBUG = True

    # Local SQLite DB
    SQLALCHEMY_DATABASE_URI = "sqlite:///pittstate_connect_dev.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail (stub for local testing)
    MAIL_SERVER = "localhost"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "no-reply@pittstate-connect.local"

    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=3)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # Static + uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    # AI Helper placeholder
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_HELPER_ENABLED = bool(OPENAI_API_KEY)

    # Branding (local)
    APP_NAME = "PittState-Connect [DEV]"
    UNIVERSITY_NAME = "Pittsburg State University"
    THEME_COLOR_PRIMARY = "#A6192E"
    THEME_COLOR_SECONDARY = "#FFB81C"

    # Dev logging
    LOG_LEVEL = "DEBUG"
