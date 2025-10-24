import os
from . import BaseConfig, PSU_BRAND_DEFAULT


class TestConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False  # make form tests easier

    # Fast tests: minimal caching + simple sessions
    CACHE_TYPE = "SimpleCache"
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SECURE = False

    # Deterministic brand for snapshots
    PSU_BRAND = PSU_BRAND_DEFAULT.copy()

    SENTRY_ENVIRONMENT = "testing"
