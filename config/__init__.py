import os
import logging

# Smart dynamic environment config loader for PittState-Connect

env = os.getenv("FLASK_ENV", "production").lower()

try:
    if env == "production":
        from config.config_production import ConfigProduction as Config
        logging.info("🏭 Using Production Configuration.")
    elif env == "development":
        from config.config_development import ConfigDevelopment as Config
        logging.info("🧩 Using Development Configuration.")
    else:
        from config.config_base import ConfigBase as Config
        logging.info("⚙️ Using Base Configuration.")
except Exception as e:
    logging.error(f"❌ Failed to import environment config: {e}")
    from config.config_base import ConfigBase as Config

__all__ = ["Config"]
