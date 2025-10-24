import os
from . import BaseConfig, PSU_BRAND_DEFAULT


class ProdConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = False

    # Render sets DATABASE_URL with postgres:// — SQLAlchemy accepts it
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", BaseConfig.SQLALCHEMY_DATABASE_URI)

    # Sessions: prefer Redis in prod if available
    if os.getenv("REDIS_URL"):
        SESSION_TYPE = "redis"
        SESSION_REDIS = os.getenv("REDIS_URL")

    # Stricter cookies in prod
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Cache: allow easy swap to RedisCache or Memcached
    CACHE_TYPE = os.getenv("CACHE_TYPE", BaseConfig.CACHE_TYPE)
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # Logging level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Brand (can be overridden by env)
    PSU_BRAND = {
        **PSU_BRAND_DEFAULT,
        "crimson": os.getenv("PSU_COLOR_CRIMSON", PSU_BRAND_DEFAULT["crimson"]),
        "gold": os.getenv("PSU_COLOR_GOLD", PSU_BRAND_DEFAULT["gold"]),
        "accent": os.getenv("PSU_COLOR_ACCENT", PSU_BRAND_DEFAULT["accent"]),
        "tagline": os.getenv("PSU_TAGLINE", PSU_BRAND_DEFAULT["tagline"]),
        "favicon": os.getenv("PSU_FAVICON", PSU_BRAND_DEFAULT["favicon"]),
    }

    # CORS: lock down to explicit origins in prod by default
    _origins = os.getenv("CORS_ORIGINS", "")
    if not _origins or _origins.strip() == "*":
        # If you truly want *, set CORS_ORIGINS="*"
        CORS_ORIGINS = ["https://pittstate-connect.onrender.com"]
    else:
        CORS_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]

    # Sentry environment tag
    SENTRY_ENVIRONMENT = "production"

    # Stronger CSP base (nonce still added at runtime)
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": ["'self'", "data:", "https://*"],
        "script-src": ["'self'"],  # nonce added later
        "style-src": ["'self'", "'unsafe-inline'"],
        "connect-src": [
            "'self'",
            "https://api.openai.com",
            "https://*.amazonaws.com",
            "https://pittstate-connect.onrender.com",
        ],
        "font-src": ["'self'", "data:"],
        "frame-ancestors": ["'none'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
    }
