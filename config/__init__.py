# ================================================================
#  PittState-Connect Configuration Loader (Advanced Final Version)
# ================================================================

import os
from loguru import logger
from flask_talisman import Talisman

# Config variants
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig


def select_config():
    """Select the configuration class dynamically."""
    env = os.getenv("FLASK_ENV", "production").lower()
    logger.info(f"Selecting configuration for environment: {env}")
    if env == "development":
        return DevConfig
    elif env == "testing":
        return TestConfig
    return ProdConfig


def attach_nonce(response):
    """Inject CSP nonce for inline scripts (used by Flask-Talisman)."""
    nonce = getattr(response, "csp_nonce", None)
    if nonce:
        response.headers["Content-Security-Policy"] = (
            response.headers.get("Content-Security-Policy", "")
            + f" 'nonce-{nonce}'"
        )
    return response


def boot_sentry(app):
    """
    Boot Sentry for error tracking, only if `sentry-sdk` and DSN exist.
    Avoids crashing when SDK isn't installed.
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        logger.info("No Sentry DSN found — skipping error tracking.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.8,
            environment=os.getenv("FLASK_ENV", "production"),
        )
        logger.info("✅ Sentry initialized successfully.")
    except ImportError:
        logger.warning("⚠️  sentry-sdk not installed — skipping Sentry setup.")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


__all__ = ["select_config", "attach_nonce", "boot_sentry"]
