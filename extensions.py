# ==============================================================
# Gorilla-Link / Pitt State Connect
# extensions.py — Centralized Flask Extension Initialization
# ==============================================================
# Features:
# ✅ Prevents circular imports (e.g., models <-> app_pro)
# ✅ Clean, modular extension registration
# ✅ Used across blueprints, utils, and models safely
# ==============================================================

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --------------------------------------------------------------
# EXTENSION INSTANCES (UNINITIALIZED)
# --------------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
login_manager = LoginManager()

# --------------------------------------------------------------
# OPTIONAL: DEFAULT LOGIN CONFIG
# --------------------------------------------------------------
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# --------------------------------------------------------------
# HELPER FUNCTION FOR INITIALIZATION
# --------------------------------------------------------------
def init_extensions(app):
    """Initialize all Flask extensions with the given app context."""
    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)

    print("✅ Flask extensions initialized successfully.")
