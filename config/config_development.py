"""
PittState-Connect | Development Configuration
Mirrors production setup for local testing and debugging.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class config_development:
    # ======================================================
    # 🧠 Core App Settings
    # ======================================================
    ENV = "development"
    DEBUG = True
    TESTING = True
    SECRET_KEY = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")

    # ======================================================
    # 🗄️ Database (Local or Render Dev)
    # ======================================================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost/pittstate_connect_dev"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 3,
    }

    # ======================================================
    # 📧 Mail Configuration
    # ======================================================
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER", "PittState Connect <noreply@pittstate.edu>"
    )

    # ======================================================
    # 🔑 OAuth / Google Login
    # ======================================================
    OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
    OAUTH_ALLOWED_DOMAIN = os.getenv("OAUTH_ALLOWED_DOMAIN", "gus.pittstate.edu")

    # ======================================================
    # 🧠 Flask-Login
    # ======================================================
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SESSION_PROTECTION = "strong"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # local dev can use http

    # ======================================================
    # 🧱 Redis / Caching
    # ======================================================
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TYPE = os.getenv("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 120

    # fallback for local no-redis testing
    if CACHE_TYPE.lower() != "rediscache":
        CACHE_TYPE = "SimpleCache"

    # ======================================================
    # 📅 APScheduler
    # ======================================================
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/Chicago"

    # ======================================================
    # 🧩 Flask-Limiter (optional rate limiting)
    # ======================================================
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "200 per hour"

    # ======================================================
    # 📊 Logging / Analytics
    # ======================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

    # ======================================================
    # 🦍 PSU Branding
    # ======================================================
    SITE_NAME = "PittState-Connect (Dev)"
    SITE_TAGLINE = "Connecting Gorillas — Students, Alumni & Employers"
    SUPPORT_EMAIL = "support@pittstate.edu"

    # ======================================================
    # 🛠 Maintenance & Feature Toggles
    # ======================================================
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"
    FEATURE_ANALYTICS_ENABLED = True
    FEATURE_SCHOLARSHIPS_PHASE2 = True
    FEATURE_EMPLOYER_PORTAL = True
    FEATURE_DONOR_DASHBOARD = True

    # ======================================================
    # 🧾 File Paths / Static
    # ======================================================
    IMAGE_LINKS_URL = os.getenv("IMAGE_LINKS_URL", "data/image_links.json")
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"

    # ======================================================
    # 🪪 Admin Defaults
    # ======================================================
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "cvandenberg@gus.pittstate.edu")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Connor")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "BballRocks1!")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "gorillalink2025")

    # ======================================================
    # 🌐 Other System Flags
    # ======================================================
    PREFERRED_URL_SCHEME = "http"
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    JSON_AS_ASCII = False
    PROPAGATE_EXCEPTIONS = True
