from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()

# Limiter uses Redis storage via config.RATELIMIT_STORAGE_URI
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# Login settings
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"  # adjust to your auth blueprint route
