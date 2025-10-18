import os
from datetime import timedelta

def _bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PROD")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Redis-backed sessions (optional)
    SESSION_TYPE = "filesystem"  # switch to "redis" if you wire it up in code
    SESSION_USE_SIGNER = True

    # Mail (if used)
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

    # Ratelimits
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200/hour")

    # App
    SITE_NAME = "PittState Connect"

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False

def get_config():
    env = os.getenv("FLASK_ENV", "production").lower()
    return DevConfig if env.startswith("dev") else ProdConfig
