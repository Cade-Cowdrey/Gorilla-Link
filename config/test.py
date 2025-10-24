# /config/test.py
import os

class TestConfig:
    """Testing configuration for automated tests."""
    DEBUG = False
    TESTING = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False

    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = "test@pittstateconnect.local"

    REDIS_URL = "redis://localhost:6379/1"

    TALISMAN_FORCE_HTTPS = False
    TALISMAN_CONTENT_SECURITY_POLICY = {"default-src": "'self'"}

    OPENAI_API_KEY = "test-key"
    OPENAI_MODEL = "gpt-4o-mini"

    LOG_LEVEL = "CRITICAL"
