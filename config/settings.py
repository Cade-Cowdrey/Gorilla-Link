import os
from datetime import timedelta


def _bool(v: str, default=False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PROD")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = _bool(os.getenv("DEBUG", "false"), False)

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions
    SESSION_TYPE = "redis" if os.getenv("REDIS_URL") else "filesystem"
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Caching
    CACHE_TYPE = "RedisCache" if os.getenv("REDIS_URL") else "SimpleCache"
    CACHE_REDIS_URL = os.getenv("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 300

    # Ratelimits
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200/hour")

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool(os.getenv("MAIL_USE_TLS", "true"), True)
    MAIL_USE_SSL = _bool(os.getenv("MAIL_USE_SSL", "false"), False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "PittState Connect <noreply@pittstate.edu>")

    # OAuth
    OAUTH_ALLOWED_DOMAIN = os.getenv("OAUTH_ALLOWED_DOMAIN", "gus.pittstate.edu")
    OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")

    # App flags
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    IMAGE_LINKS_URL = os.getenv("IMAGE_LINKS_URL", "data/image_links.json")
