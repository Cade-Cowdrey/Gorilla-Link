import os
from . import BaseConfig, PSU_BRAND_DEFAULT


class DevConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

    # Local sqlite by default
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/dev.db")

    # Cookies: easier local testing
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"

    # CORS: allow all in dev
    CORS_ORIGINS = "*"

    # Brand (dev can use alternate accent for visibility)
    PSU_BRAND = {
        **PSU_BRAND_DEFAULT,
        "accent": os.getenv("PSU_COLOR_ACCENT", "#D7A22A"),
        "tagline": os.getenv("PSU_TAGLINE", "PittState-Connect — Dev"),
    }

    SENTRY_ENVIRONMENT = "development"

    # Slightly looser CSP (still nonce-enforced at runtime)
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": ["'self'", "data:", "https://*"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "connect-src": ["'self'", "http://localhost:*", "https://*"],
        "font-src": ["'self'", "data:"],
        "frame-ancestors": ["'none'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
    }
