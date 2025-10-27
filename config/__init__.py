"""
PittState-Connect | Config Loader
Auto-selects correct configuration based on environment and ensures all required keys are set.
Supports: Development, Production, and Testing environments.
"""

import os
from loguru import logger

# ======================================================
# 🔧 Environment Detection
# ======================================================
env = os.getenv("FLASK_ENV", "production").lower()
logger.info(f"🧭 Loading configuration for environment: {env}")

try:
    if env == "development":
        from config.config_development import config_development as Config
        logger.info("🧱 Using Development Configuration (Debug mode).")
    elif env == "testing":
        from config.config_testing import config_testing as Config
        logger.info("🧪 Using Testing Configuration.")
    else:
        from config.config_production import config_production as Config
        logger.info("🏭 Using Production Configuration.")
except ImportError as e:
    logger.error(f"❌ Failed to import environment config: {e}")
    from config.config_production import config_production as Config
    logger.warning("⚠️ Falling back to Production Configuration.")


# ======================================================
# 🧩 Global Validation + Fallback Defaults
# ======================================================
def ensure_core_settings(app):
    """Ensure critical production values are loaded correctly."""
    required_keys = [
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "REDIS_URL",
        "MAIL_SERVER",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
    ]

    for key in required_keys:
        if not app.config.get(key):
            logger.warning(f"⚠️ Missing config: {key}. Setting safe default.")
            if key == "SECRET_KEY":
                app.config[key] = "fallback-dev-secret-key"
            elif key == "SQLALCHEMY_DATABASE_URI":
                app.config[key] = os.getenv("DATABASE_URL", "")
            elif key == "REDIS_URL":
                app.config[key] = os.getenv("REDIS_URL", "redis://localhost:6379")
            elif key == "MAIL_SERVER":
                app.config[key] = "smtp.gmail.com"
            elif key == "MAIL_USERNAME":
                app.config[key] = os.getenv("MAIL_USERNAME", "")
            elif key == "MAIL_PASSWORD":
                app.config[key] = os.getenv("MAIL_PASSWORD", "")

    # Optional Enhancements
    app.config.setdefault("ENABLE_ANALYTICS", True)
    app.config.setdefault("ENABLE_AI_ASSISTANT", True)
    app.config.setdefault("MAINTENANCE_MODE", False)

    logger.info("✅ Core settings validated successfully.")
    return app


# ======================================================
# 🧠 Export Utility
# ======================================================
def load_config(app):
    """Apply environment-based config and ensure consistency."""
    app.config.from_object(Config)
    ensure_core_settings(app)
    logger.info("🦍 PittState-Connect configuration applied successfully.")
    return app


# ======================================================
# 🧾 Export Config Class for app_pro.py
# ======================================================
config = Config
