# ===============================================================
#  PittState-Connect — Centralized Configuration (Final + Security)
#  File: config.py
#  ---------------------------------------------------------------
#  - Environment-specific config classes
#  - Feature flags & strict security headers
#  - Sentry integration helper
#  - CSP Nonce injector for inline script safety
# ===============================================================

from __future__ import annotations
import os
import secrets
import logging
from datetime import timedelta
from typing import Optional

# ---------------------------------------------------------------
#  Helper Functions
# ---------------------------------------------------------------
def _bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "t", "yes", "y", "on")

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [x.strip() for x in raw.split(",") if x.strip()]

def _maybe_redis():
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url)
    except Exception:
        return None


# ---------------------------------------------------------------
#  Base Configuration
# ---------------------------------------------------------------
class BaseConfig:
    """Shared defaults for all environments."""

    # ---- Core App ----
    APP_NAME = "PittState-Connect"
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    DEBUG = False
    TESTING = False

    # ---- Database ----
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate_connect.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": _int("DB_POOL_RECYCLE", 1800),
        "pool_size": _int("DB_POOL_SIZE", 5),
        "max_overflow": _int("DB_MAX_OVERFLOW", 10),
    }

    # ---- Templates / JSON ----
    TEMPLATES_AUTO_RELOAD = _bool("TEMPLATES_AUTO_RELOAD", True)
    JSON_SORT_KEYS = False

    # ---- Mail ----
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = _int("MAIL_PORT", 587)
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.edu")

    # ---- Sessions ----
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SESSION_PERMANENT = _bool("SESSION_PERMANENT", False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=_int("SESSION_DAYS", 7))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", True)
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR", "/tmp/flask_sessions")
    SESSION_REDIS = _maybe_redis()

    # ---- CORS ----
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ORIGINS = _list("CORS_ORIGINS", ["https://pittstate-connect.onrender.com"])
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-PSU-Role"]

    # ---- Compression ----
    COMPRESS_ALGORITHM = os.getenv("COMPRESS_ALGORITHM", "br")
    COMPRESS_LEVEL = _int("COMPRESS_LEVEL", 6)

    # ---- Security: Talisman + CSP ----
    TALISMAN_ENABLED = _bool("TALISMAN_ENABLED", True)
    TALISMAN_FORCE_HTTPS = _bool("TALISMAN_FORCE_HTTPS", True)
    TALISMAN_FRAME_OPTIONS = "SAMEORIGIN"

    # Baseline strict Content Security Policy
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https:"],
        "style-src": ["'self'", "'unsafe-inline'", "https:"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'", "https:", "data:"],
        "connect-src": ["'self'", "https:"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "frame-ancestors": ["'self'"],
    }

    # ---- AI / OpenAI ----
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    FEATURE_AI = _bool("FEATURE_AI", True)

    # ---- Redis / Cache ----
    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = _int("CACHE_DEFAULT_TIMEOUT", 300)

    # ---- Rate Limits ----
    API_RATE_LIMIT = _int("API_RATE_LIMIT", 60)
    API_RATE_WINDOW = _int("API_RATE_WINDOW", 60)

    # ---- Monitoring ----
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_TRACES_SAMPLE_RATE = _float("SENTRY_TRACES_SAMPLE_RATE", 0.05)
    SENTRY_PROFILES_SAMPLE_RATE = _float("SENTRY_PROFILES_SAMPLE_RATE", 0.0)

    # ---- Branding ----
    PSU_BRAND = {
        "name": "PittState-Connect",
        "tagline": "Connecting Gorillas for Life 🦍",
        "crimson": "#A6192E",
        "gold": "#FFB81C",
    }

    # ---- Feature Flags ----
    FEATURE_SCHOLARSHIPS = _bool("FEATURE_SCHOLARSHIPS", True)
    FEATURE_JOBS = _bool("FEATURE_JOBS", True)
    FEATURE_EVENTS = _bool("FEATURE_EVENTS", True)
    FEATURE_COMMUNITY = _bool("FEATURE_COMMUNITY", True)
    FEATURE_ALUMNI = _bool("FEATURE_ALUMNI", True)
    FEATURE_ANALYTICS = _bool("FEATURE_ANALYTICS", True)
    FEATURE_AI_ASSISTANT = _bool("FEATURE_AI_ASSISTANT", True)

    # ---- Scheduler ----
    SCHED_TIMEZONE = os.getenv("SCHED_TIMEZONE", "US/Central")

    # ---- CSP Nonce (auto-generated per request)
    CSP_NONCE_KEY = "csp_nonce"

    @staticmethod
    def generate_nonce() -> str:
        """Generate a unique nonce for inline scripts/styles."""
        return secrets.token_urlsafe(16)


# ---------------------------------------------------------------
#  Environment-Specific Configs
# ---------------------------------------------------------------
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev_pittstate_connect.db")
    CORS_ORIGINS = _list("CORS_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"])
    TALISMAN_CONTENT_SECURITY_POLICY = {
        **BaseConfig.TALISMAN_CONTENT_SECURITY_POLICY,
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https:"],
    }


class StagingConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", BaseConfig.SQLALCHEMY_DATABASE_URI)
    CORS_ORIGINS = _list("CORS_ORIGINS", ["*"])


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    TALISMAN_FORCE_HTTPS = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", BaseConfig.SQLALCHEMY_DATABASE_URI)
    CORS_ORIGINS = _list("CORS_ORIGINS", ["https://pittstate-connect.onrender.com"])


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TALISMAN_ENABLED = False
    FEATURE_AI = False
    CORS_ORIGINS = ["http://localhost"]
    SESSION_COOKIE_SECURE = False


# ---------------------------------------------------------------
#  Config Selector
# ---------------------------------------------------------------
def select_config() -> type[BaseConfig]:
    env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production").lower()
    if env in ("dev", "development"):
        return DevelopmentConfig
    if env in ("stage", "staging"):
        return StagingConfig
    if env in ("test", "testing"):
        return TestingConfig
    return ProductionConfig


# ---------------------------------------------------------------
#  Security Enhancements — CSP Nonce & Sentry Boot
# ---------------------------------------------------------------
def attach_nonce(app):
    """Attach a per-request CSP nonce for secure inline scripts."""
    from flask import g, request

    @app.before_request
    def _generate_nonce():
        g.csp_nonce = app.config["generate_nonce"]() if callable(app.config.get("generate_nonce")) else secrets.token_urlsafe(16)

    @app.context_processor
    def inject_nonce():
        return {"csp_nonce": getattr(g, "csp_nonce", "")}


def boot_sentry(app):
    """Initialize Sentry with Flask integration (if DSN provided)."""
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        app.logger.info("🟡 Sentry DSN not set — skipping setup.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=app.config.get("SENTRY_TRACES_SAMPLE_RATE", 0.05),
            profiles_sample_rate=app.config.get("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
            environment=os.getenv("APP_ENV", "production"),
            release=os.getenv("RENDER_GIT_COMMIT", "unknown"),
        )
        app.logger.info("🧠 Sentry monitoring initialized successfully.")
    except Exception as e:
        app.logger.warning(f"Sentry setup failed: {e}")
