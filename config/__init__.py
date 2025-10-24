# ============================================================
#  config/__init__.py — PittState-Connect Configuration
# ============================================================

import os
from dotenv import load_dotenv
from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
import redis

# Load environment variables
load_dotenv()


# ------------------------------------------------------------
#  Base Config
# ------------------------------------------------------------
class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = os.getenv("SESSION_TYPE", "redis")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "psu_sess:"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Caching
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.edu")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # OpenAI / AI Features
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Security
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https://*"],
        "connect-src": ["'self'", "https://api.openai.com"],
    }

    SCHEDULER_API_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours


# ------------------------------------------------------------
#  Environment-specific configs
# ------------------------------------------------------------
class DevConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = "development"


class ProdConfig(BaseConfig):
    DEBUG = False
    FLASK_ENV = "production"


# ------------------------------------------------------------
#  Helper Functions
# ------------------------------------------------------------
def select_config():
    env = os.getenv("FLASK_ENV", "production")
    print(f"[config] Selecting configuration for environment: {env}")
    if env == "development":
        return DevConfig
    return ProdConfig


def attach_nonce(response):
    """Attach a CSP nonce to support inline scripts in templates."""
    nonce = os.urandom(16).hex()
    response.headers["Content-Security-Policy"] = (
        response.headers.get("Content-Security-Policy", "")
        + f" 'nonce-{nonce}'"
    )
    return response


def boot_sentry(app):
    """Initialize Sentry error tracking (if DSN provided)."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        print("[config] No Sentry DSN found — skipping error tracking.")
        return
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment=app.config.get("FLASK_ENV"),
    )
    print("[config] Sentry initialized successfully.")


# ------------------------------------------------------------
#  Redis Session Helper
# ------------------------------------------------------------
def bind_redis_session(app):
    """Bind a real Redis client to Flask-Session to prevent 'str.setex' errors."""
    if app.config.get("SESSION_TYPE") == "redis":
        redis_url = app.config.get("REDIS_URL")
        try:
            redis_client = redis.from_url(redis_url)
            app.config["SESSION_REDIS"] = redis_client
            print(f"[config] Redis session bound → {redis_url}")
        except Exception as e:
            print(f"[config] Failed to bind Redis session: {e}")
