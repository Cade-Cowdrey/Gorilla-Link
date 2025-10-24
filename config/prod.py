# /config/prod.py
import os

class ProdConfig:
    """Production configuration for PittState-Connect (Render / PSU server)."""
    DEBUG = False
    TESTING = False

    # Secure Database (Render or AWS RDS)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secrets and sessions
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "psc_session:"
    REDIS_URL = os.getenv("REDIS_URL")

    # Flask-Mail (SendGrid recommended)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

    # Flask-Talisman (Strict HTTPS + CSP)
    TALISMAN_FORCE_HTTPS = True
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": ["'self'", "data:", "https:"],
        "script-src": ["'self'", "'nonce-*'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "connect-src": ["'self'", "https://api.openai.com"],
    }

    # OpenAI Integration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # AWS S3 or compatible cloud bucket
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "pittstate-connect-bucket")

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/pittstate-connect.log")

    # Scheduler & Analytics
    SCHEDULER_API_ENABLED = True
    ANALYTICS_CACHE_TTL = 900  # 15 min Redis cache
    ANALYTICS_SNAPSHOT_INTERVAL_HOURS = 6

    # Security headers
    SECURE_COOKIES = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
