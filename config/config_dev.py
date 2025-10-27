"""
PittState-Connect | config/config_dev.py
Local development configuration with safe defaults and full feature parity.
"""

import os
from datetime import timedelta

class Config:
    # ------------------------------------------------------------------
    # 🔧 Core Flask Settings
    # ------------------------------------------------------------------
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-psu-key")
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # ------------------------------------------------------------------
    # 🗄️ Local Database (SQLite)
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate_connect_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------
    # 💌 Development Mail System (Mailtrap / Console)
    # ------------------------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "sandbox.smtp.mailtrap.io")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 2525))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-mailtrap-username")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-mailtrap-password")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "dev@pittstate-connect.local")

    # Optional: use console for local emails
    MAIL_SUPPRESS_SEND = False
    TESTING = False

    # ------------------------------------------------------------------
    # ⚡ Local Cache / Redis Fallback
    # ------------------------------------------------------------------
    REDIS_URL = os.getenv("REDIS_URL", "")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        CACHE_TYPE = "SimpleCache"
        CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = 500

    # ------------------------------------------------------------------
    # ⏰ APScheduler (still enabled in dev)
    # ------------------------------------------------------------------
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 2}}
    SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 1}

    # ------------------------------------------------------------------
    # 🤖 AI / Smart Assistant (optional in dev)
    # ------------------------------------------------------------------
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ASSISTANT_ENABLED = bool(OPENAI_API_KEY)

    # ------------------------------------------------------------------
    # 🧮 Analytics / Dashboards (can be toggled for dev testing)
    # ------------------------------------------------------------------
    ENABLE_ANALYTICS_DASHBOARD = True
    ENABLE_DONOR_PORTAL = True
    ENABLE_SCHOLARSHIP_AI_HELPER = True
    ENABLE_FINANCIAL_LITERACY_HUB = True

    # ------------------------------------------------------------------
    # 🦍 PittState Branding (shared constants)
    # ------------------------------------------------------------------
    PSU_BRAND_PRIMARY = "#BA0C2F"
    PSU_BRAND_SECONDARY = "#F1B434"
    PSU_BRAND_DARK = "#2B2B2B"
    PSU_TAGLINE = "PittState-Connect (DEV) | Empowering Gorillas for Life"

    # ------------------------------------------------------------------
    # 🧰 Logging / Debugging
    # ------------------------------------------------------------------
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

    # ------------------------------------------------------------------
    # 📎 Local File Uploads
    # ------------------------------------------------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "docx"}

    # ------------------------------------------------------------------
    # 🌎 CORS / Frontend Testing
    # ------------------------------------------------------------------
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_HEADERS = "Content-Type"
    PREFERRED_URL_SCHEME = "http"

    # ------------------------------------------------------------------
    # 📡 Developer Options
    # ------------------------------------------------------------------
    ENABLE_FACULTY_API = True
    ENABLE_ALUMNI_API = True
    ENABLE_EMPLOYER_API = True
    ENABLE_SCHOLARSHIP_MATCHER = True
    ENABLE_COST_TO_COMPLETION_DASHBOARD = True

    # ------------------------------------------------------------------
    # 💾 JSON / Response Tweaks
    # ------------------------------------------------------------------
    JSON_SORT_KEYS = False

# Export class
DevelopmentConfig = Config
