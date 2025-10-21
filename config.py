import os
from pathlib import Path
from datetime import timedelta


class BaseConfig:
    """Shared defaults across all environments."""
    # --- App ---
    APP_NAME = "PittState-Connect"
    SECRET_KEY = os.environ.get("SECRET_KEY")  # REQUIRED in Prod

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")  # REQUIRED
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- Redis / Cache ---
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")  # "RedisCache" in prod
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "120"))

    # --- Security / CSRF / CORS ---
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    # When behind a proxy (Render), trust X-Forwarded-Proto for https
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")

    # --- Rate Limiting ---
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200/hour")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", REDIS_URL)

    # --- Logging ---
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # --- Mail (optional, used by digests/alerts) ---
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587")) if os.environ.get("MAIL_PORT") else None
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@pittstate.edu")

    # --- JWT / API ---
    API_JWT_SECRET = os.environ.get("API_JWT_SECRET")  # REQUIRED if API enabled
    API_DEFAULT_EXP = timedelta(hours=8)

    # --- Feature Flags ---
    ENABLE_BLUEPRINT_AUTODISCOVERY = os.environ.get("ENABLE_BLUEPRINT_AUTODISCOVERY", "true").lower() == "true"
    ENABLE_API = os.environ.get("ENABLE_API", "true").lower() == "true"

    # --- Templating ---
    TEMPLATES_AUTO_RELOAD = os.environ.get("TEMPLATES_AUTO_RELOAD", "false").lower() == "true"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    CACHE_TYPE = "SimpleCache"
    RATELIMIT_DEFAULT = "1000/hour"
    PREFERRED_URL_SCHEME = "http"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = "NullCache"
    RATELIMIT_ENABLED = False
    ENABLE_API = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Stronger cookie settings in prod
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Recommended: Redis-backed cache in prod
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL", BaseConfig.REDIS_URL)


def load_config() -> BaseConfig:
    env = os.environ.get("FLASK_ENV", "production").lower()
    if env in ("dev", "development"):
        return DevelopmentConfig()
    if env in ("test", "testing"):
        return TestingConfig()
    return ProductionConfig()


def validate_config(cfg: BaseConfig):
    """Fail fast on missing critical secrets in production-like envs."""
    env = os.environ.get("FLASK_ENV", "production").lower()
    is_prod_like = env not in ("dev", "development", "test", "testing")

    missing = []
    if not cfg.SQLALCHEMY_DATABASE_URI:
        missing.append("DATABASE_URL")
    if is_prod_like and not cfg.SECRET_KEY:
        missing.append("SECRET_KEY")
    if cfg.ENABLE_API and is_prod_like and not cfg.API_JWT_SECRET:
        missing.append("API_JWT_SECRET")

    if missing:
        raise RuntimeError(
            f"Invalid configuration: missing required environment variables: {', '.join(missing)}"
        )
