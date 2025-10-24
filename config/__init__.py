"""
Central config selector + runtime helpers (CSP nonce injection, Sentry bootstrap).
Safe for local dev, Docker, and Render.
"""

from __future__ import annotations
import os
import secrets
from typing import Type, Optional

from flask import g, request


# -------- Brand (fallback so templates never break) --------
PSU_BRAND_DEFAULT = {
    "crimson": "#A6192E",
    "gold": "#FFB81C",
    "gray": "#5A5A5A",
    "white": "#FFFFFF",
    "black": "#000000",
    "accent": "#D7A22A",
    "gradient": "linear-gradient(90deg, #A6192E 0%, #FFB81C 100%)",
    "tagline": "PittState-Connect — Linking Gorillas for Life",
    "favicon": "/static/images/psu_logo.png",
}


# -------- Environment selection --------
def _env_name() -> str:
    # Priority: CONFIG_NAME > FLASK_ENV > APP_ENV > RENDER (implies production) > default dev
    name = os.getenv("CONFIG_NAME") or os.getenv("FLASK_ENV") or os.getenv("APP_ENV")
    if name:
        return name.lower()

    if os.getenv("RENDER"):  # Render dynos set this
        return "production"

    return "development"


def select_config() -> Type["BaseConfig"]:
    env = _env_name()
    try:
        if env in ("prod", "production"):
            from .prod import ProdConfig

            cfg = ProdConfig
        elif env in ("test", "testing"):
            from .test import TestConfig

            cfg = TestConfig
        else:
            from .dev import DevConfig

            cfg = DevConfig

        # small log line without importing logging handlers prematurely
        print(f"[config] Selecting configuration for environment: {env}")
        return cfg
    except Exception as e:
        print(f"[config] Failed to import specific config ({env}): {e} — falling back to DevConfig")
        from .dev import DevConfig

        return DevConfig


# -------- CSP nonce helper (wired in app.after_request) --------
def _ensure_request_nonce() -> str:
    # this gives us a per-request random nonce for inline scripts (where needed)
    if not hasattr(g, "csp_nonce") or not g.csp_nonce:
        g.csp_nonce = secrets.token_urlsafe(16)
    return g.csp_nonce


def attach_nonce(response):
    """
    Append a nonce to CSP for this response. Works with or without Flask-Talisman present.
    Keeps existing CSP if Talisman already set one; otherwise writes a reasonable default.
    """
    nonce = _ensure_request_nonce()

    existing_csp = response.headers.get("Content-Security-Policy")
    if existing_csp:
        # naive but effective augmentation: add script/style nonces if not present
        if "script-src" in existing_csp and f"'nonce-{nonce}'" not in existing_csp:
            existing_csp = existing_csp.replace(
                "script-src",
                f"script-src 'nonce-{nonce}'",
                1,
            )
        else:
            # add a new directive if missing
            existing_csp += f"; script-src 'self' 'nonce-{nonce}' 'strict-dynamic'"

        if "style-src" not in existing_csp:
            existing_csp += "; style-src 'self' 'unsafe-inline'"
        response.headers["Content-Security-Policy"] = existing_csp
    else:
        # baseline CSP if none set
        response.headers[
            "Content-Security-Policy"
        ] = f"default-src 'self'; img-src 'self' data: https://*; script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; style-src 'self' 'unsafe-inline'"

    # enable powerful XSS protection headers regardless
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

    return response


# -------- Sentry bootstrap (optional) --------
def boot_sentry(app) -> None:
    """
    Lazily initialize Sentry if SENTRY_DSN is present. Safe no-op if the package is not installed.
    """
    dsn = app.config.get("SENTRY_DSN") or os.getenv("SENTRY_DSN")
    environment = app.config.get("SENTRY_ENVIRONMENT") or _env_name()

    if not dsn:
        print("[config] No Sentry DSN found — skipping error tracking.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(level=None, event_level=None),
            ],
            send_default_pii=False,
        )
        print("[config] Sentry initialized.")
    except ImportError:
        print("[config] sentry_sdk not installed — skipping error tracking.")
    except Exception as e:
        print(f"[config] Sentry init error: {e}")


# -------- Base config shared helpers --------
class BaseConfig:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    APP_NAME = "PittState-Connect"

    # Flask
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = "https"
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB uploads
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = False

    # Logging (string level)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")  # set to 'redis' when REDIS_URL present
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_HOURS", "8")) * 60 * 60

    # CORS
    # Accept: "*" or comma-separated list (https://example.com,https://foo.bar)
    _origins = os.getenv("CORS_ORIGINS", "*")
    if _origins.strip() == "*":
        CORS_ORIGINS = "*"
    else:
        CORS_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]

    # Cache
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # APScheduler
    SCHEDULER_API_ENABLED = True

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate.edu")

    # AWS / S3 (optional)
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL")  # optional CDN URL

    # Redis (optional)
    REDIS_URL = os.getenv("REDIS_URL")

    # OpenAI (optional)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Sentry (optional)
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT")

    # Flask-Talisman CSP (baseline; nonce appended at runtime)
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": ["'self'", "data:", "https://*"],
        "script-src": ["'self'"],  # nonce added in attach_nonce
        "style-src": ["'self'", "'unsafe-inline'"],
        "connect-src": ["'self'", "https://*"],
        "font-src": ["'self'", "data:"],
        "frame-ancestors": ["'none'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
    }

    # PSU brand injected via templates; keep a server-side copy for convenience
    PSU_BRAND = PSU_BRAND_DEFAULT.copy()
