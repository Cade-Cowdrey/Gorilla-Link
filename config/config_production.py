import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    
    # --- OAuth Providers (Social Login) ---
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
    MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
    
    # --- External API Keys ---
    # Scholarship APIs
    SCHOLARSHIPS_COM_API_KEY = os.getenv("SCHOLARSHIPS_COM_API_KEY")
    FASTWEB_API_KEY = os.getenv("FASTWEB_API_KEY")
    COLLEGE_BOARD_API_KEY = os.getenv("COLLEGE_BOARD_API_KEY")
    
    # Video Conferencing
    ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
    ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
    ZOOM_WEBHOOK_SECRET = os.getenv("ZOOM_WEBHOOK_SECRET")
    
    # Calendar Integration
    GOOGLE_CALENDAR_CREDENTIALS = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    MICROSOFT_GRAPH_API_KEY = os.getenv("MICROSOFT_GRAPH_API_KEY")

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
