# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Flask Extensions Initialization (Production Ready)
# ---------------------------------------------------------
import os
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache

# ---------------------------------------------------------
# Instantiate Core Extensions
# ---------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()

# ---------------------------------------------------------
# Redis-Backed Cache (with local fallback)
# ---------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    cache_config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": REDIS_URL,
        "CACHE_DEFAULT_TIMEOUT": 600,  # 10 minutes
    }
    print("⚡ Using Redis cache backend (Render)")
else:
    cache_config = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
    }
    print("💾 Using SimpleCache backend (local fallback)")

cache = Cache(config=cache_config)

# ---------------------------------------------------------
# Flask-Login Configuration
# ---------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user object from the database for active sessions.
    """
    from models import User
    return User.query.get(int(user_id))


# ---------------------------------------------------------
# Flask-Login Defaults
# ---------------------------------------------------------
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.session_protection = "strong"

print("✅ Extensions initialized successfully.")
