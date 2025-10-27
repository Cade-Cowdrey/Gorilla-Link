"""
config/mail_config.py
--------------------------------------------------
PittState-Connect | Production Mail Configuration
Supports SendGrid (preferred) and Flask-Mail fallback.
All variables pulled securely from environment.
--------------------------------------------------
"""

import os
from loguru import logger


class MailConfig:
    """Unified email configuration for PittState-Connect."""

    # --------------------------------------------------
    # 🔐 Base Config
    # --------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"

    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", os.getenv("SENDGRID_API_KEY", ""))
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com"
    )

    # --------------------------------------------------
    # 📦 SendGrid Support
    # --------------------------------------------------
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "PittState-Connect")
    SENDGRID_TEMPLATE_PATH = "templates/emails"

    # --------------------------------------------------
    # 🧠 Logging & Analytics
    # --------------------------------------------------
    EMAIL_ANALYTICS_ENABLED = os.getenv("EMAIL_ANALYTICS_ENABLED", "True").lower() == "true"
    EMAIL_LOG_REDIS_KEY = os.getenv("EMAIL_LOG_REDIS_KEY", "email_logs")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pittstateconnect.com")

    # --------------------------------------------------
    # 📬 Rate Limiting & Safety
    # --------------------------------------------------
    MAX_EMAILS_PER_HOUR = int(os.getenv("MAX_EMAILS_PER_HOUR", 500))
    RATE_LIMIT_REDIS_KEY = "email_rate_limit"

    @classmethod
    def summary(cls):
        """Return configuration summary (for diagnostics)."""
        return {
            "MAIL_SERVER": cls.MAIL_SERVER,
            "MAIL_PORT": cls.MAIL_PORT,
            "TLS": cls.MAIL_USE_TLS,
            "SSL": cls.MAIL_USE_SSL,
            "SENDER": cls.MAIL_DEFAULT_SENDER,
            "SENDGRID_ENABLED": bool(cls.SENDGRID_API_KEY),
            "ADMIN_EMAIL": cls.ADMIN_EMAIL,
        }


# --------------------------------------------------
# 🧾 Optional Diagnostic Print (only for debugging)
# --------------------------------------------------
if __name__ == "__main__":
    summary = MailConfig.summary()
    logger.info("📨 Mail Configuration Summary:")
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")
