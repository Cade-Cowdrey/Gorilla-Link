# ================================================================
#  PittState-Connect Configuration Loader
#  Dynamically selects the appropriate environment config.
# ================================================================

import os
from loguru import logger
from flask_talisman import Talisman

# Import all configuration variants
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig


def select_config():
    """
    Automatically select the configuration class based on environment.
    Defaults to production when running on Render.
    """
    env = os.getenv("FLASK_ENV", "production").lower()
    logger.info(f"Selecting configuration for environment: {env}")

    if env == "development":
        return DevConfig
    elif env == "testing":
        return TestConfig
    else:
        return ProdConfig


def attach_nonce(response):
    """
    Flask-Talisman nonce injector for CSP-compliant inline scripts.
    """
    nonce = getattr(response, "csp_nonce", None)
    if nonce:
        response.headers["Content-Security-Policy"] = (
            response.headers.get("Content-Security-Policy", "")
            + f" 'nonce-{nonce}'"
        )
    return response


def boot_sentry(app):
    """
    Initialize Sentry (if SENTRY_DSN is present in environment).
    """
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.7,
            environment=os.getenv("FLASK_ENV", "production"),
        )
        logger.info("Sentry initialized for error tracking.")
    else:
        logger.info("Sentry DSN not found — skipping initialization.")


__all__ = ["select_config", "attach_nonce", "boot_sentry"]
