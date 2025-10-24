# /config/__init__.py
import os
from flask_talisman import Talisman
from loguru import logger

# Import your configuration classes
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig


def select_config():
    """Selects config class based on FLASK_ENV or RENDER environment."""
    env = os.getenv("FLASK_ENV", "production").lower()
    render_env = os.getenv("RENDER", "false").lower() == "true"

    if env == "development":
        logger.info("🔧 Using Development Configuration")
        return DevConfig
    elif env == "testing":
        logger.info("🧪 Using Testing Configuration")
        return TestConfig
    elif render_env or env == "production":
        logger.info("🚀 Using Production Configuration")
        return ProdConfig
    else:
        logger.warning(f"⚠️ Unknown FLASK_ENV '{env}', defaulting to Production.")
        return ProdConfig


def attach_nonce(app):
    """Attach CSP nonce for inline scripts to comply with Flask-Talisman security."""
    @app.context_processor
    def inject_nonce():
        nonce = os.urandom(16).hex()
        return dict(nonce=nonce)
    return app


def boot_sentry(app):
    """Optional: initialize Sentry or error monitoring safely."""
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        dsn = os.getenv("SENTRY_DSN")
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.8,
                environment=os.getenv("FLASK_ENV", "production")
            )
            logger.info("🪶 Sentry initialized successfully.")
        else:
            logger.warning("⚠️ Sentry DSN not provided; skipping Sentry setup.")
    except ImportError:
        logger.warning("⚠️ sentry_sdk not installed; skipping Sentry setup.")
    except Exception as e:
        logger.error(f"Sentry initialization failed: {e}")
    return app
