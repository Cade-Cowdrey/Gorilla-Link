import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from redis import Redis
from config import Config
from models import User

# --- Core extensions ---
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

# --- Redis Cache ---
redis_client = Redis.from_url(Config.REDIS_URL, decode_responses=True)

# --- Login Manager ---
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logging.error(f"❌ Error loading user: {e}")
        return None

# --- Limiter ---
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# --- Scheduler ---
scheduler = APScheduler()

# --- Initialization helper ---
def init_extensions(app):
    """Initialize all core extensions for the app."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)
    scheduler.init_app(app)
    login_manager.init_app(app)

    # Start background scheduler
    if not scheduler.running:
        scheduler.start()

    logging.info("✅ All extensions initialized successfully.")
