"""
PittState-Connect | Testing Configuration
For CI/CD pipelines, unit tests, and sandbox environments.
"""

import os
import tempfile

class config_testing:
    # Flask Core
    DEBUG = False
    TESTING = True
    SECRET_KEY = "testing-secret-key-psu"

    # Temporary SQLite database for isolated testing
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{tempfile.gettempdir()}/pittstate_connect_test.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Disable heavy integrations
    REDIS_URL = "redis://localhost:6379/1"
    ENABLE_ANALYTICS = False
    ENABLE_AI_ASSISTANT = False

    # Email — mocked for tests
    MAIL_SERVER = "localhost"
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "test@pittstate.edu"

    # Logging
    LOG_LEVEL = "WARNING"

    # Misc
    ENV = "testing"
