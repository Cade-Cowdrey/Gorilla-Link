"""
PittState-Connect | config/config_production.py
Full production configuration for Render deployment with all optional enhancements.
"""

import os
from datetime import timedelta

class Config:
    # ------------------------------------------------------------------
    # 🔐 Core Security & Flask Settings
    # ------------------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-psu-key")
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # ------------------------------------------------------------------
    # 🗄️ Database (Render PostgreSQL)
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 5,
        "max_overflow": 10,
    }

    # ------------------------------------------------------------------
    # 💌 Mail / SendGrid Integration
    # ------------------------------------------------------------------
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "apikey")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", SENDGRID_API_KEY or "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstate-connect.com")

    # ------------------------------------------------------------------
    # ⚡ Redis + Flask-Caching
    # ------------------------------------------------------------------
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes

    # ------------------------------------------------------------------
    # 📈 APScheduler (background jobs)
    # ------------------------------------------------------------------
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 3}}
    SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 1}

    # ------------------------------------------------------------------
    # 🤖 OpenAI / AI Smart Assistant Integration
    # ------------------------------------------------------------------
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ASSISTANT_ENABLED = bool(OPENAI_API_KEY)

    # ------------------------------------------------------------------
    # 🧮 Analytics / Smart Dashboard Toggles
    # ------------------------------------------------------------------
    ENABLE_ANALYTICS_DASHBOARD = True
    ENABLE_DONOR_PORTAL = True
    ENABLE_SCHOLARSHIP_AI_HELPER = True
    ENABLE_FINANCIAL_LITERACY_HUB = True
    ENABLE_DEPARTMENT_ADDITIONS = True

    # ------------------------------------------------------------------
    # 🦍 PittState Brand Identity Constants
    # ------------------------------------------------------------------
    PSU_BRAND_PRIMARY = "#BA0C2F"   # Crimson
    PSU_BRAND_SECONDARY = "#F1B434" # Gold
    PSU_BRAND_DARK = "#2B2B2B"
    PSU_TAGLINE = "PittState-Connect | Empowering Gorillas for Life"

    # ------------------------------------------------------------------
    # 🧰 Logging Configuration
    # ------------------------------------------------------------------
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

    # ------------------------------------------------------------------
    # 📡 API / Feature Gateways
    # ------------------------------------------------------------------
    ENABLE_FACULTY_API = True
    ENABLE_ALUMNI_API = True
    ENABLE_EMPLOYER_API = True
    ENABLE_SCHOLARSHIP_MATCHER = True
    ENABLE_COST_TO_COMPLETION_DASHBOARD = True

    # ------------------------------------------------------------------
    # 📎 File Uploads / Cloud Storage
    # ------------------------------------------------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "docx"}

    # ------------------------------------------------------------------
    # 🌎 CORS / Frontend Integration
    # ------------------------------------------------------------------
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_HEADERS = "Content-Type"

    # ------------------------------------------------------------------
    # 🧾 Miscellaneous
    # ------------------------------------------------------------------
    JSON_SORT_KEYS = False
    PREFERRED_URL_SCHEME = "https"

# Export class for Flask
ProductionConfig = Config
