import os
import logging

class ConfigProduction:
    """Production configuration for PittState-Connect."""

    # --- Flask Core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")
    DEBUG = False
    TESTING = False
    ENV = "production"

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Redis Cache ---
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # --- Flask-Mail ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "PittState Connect <noreply@pittstate.edu>")

    # --- OAuth (Google) ---
    OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
    OAUTH_ALLOWED_DOMAIN = os.getenv("OAUTH_ALLOWED_DOMAIN", "gus.pittstate.edu")

    # --- Rate Limiting ---
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # --- Scheduler ---
    SCHEDULER_API_ENABLED = True

    # --- Logging ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

    # --- AI Assistant ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ASSISTANT_ENABLED = True

    # --- Analytics ---
    ANALYTICS_ENABLED = True
    ANALYTICS_TRACKING_DAYS = 7

    # --- PSU Branding ---
    PSU_THEME = {
        "primary": "#990000",   # Crimson
        "secondary": "#FFD100", # Gold
        "neutral": "#212121",
    }

    @staticmethod
    def init_app(app):
        """Optional app initialization hook for production."""
        log_level = getattr(logging, ConfigProduction.LOG_LEVEL, logging.INFO)
        logging.basicConfig(level=log_level, format=ConfigProduction.LOG_FORMAT)
        logging.info("🏭 Using Production Configuration.")
