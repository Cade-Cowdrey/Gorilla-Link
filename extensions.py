import logging
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.storage import RedisStorage
from flask_apscheduler import APScheduler
from flask_caching import Cache
from flask_cors import CORS
from flask_socketio import SocketIO
from redis import Redis
from celery import Celery

# --- Core extensions ---
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
# Initialize limiter without storage - will be configured in init_extensions
limiter = Limiter(
    key_func=get_remote_address, 
    default_limits=["200 per day", "50 per hour"],
    storage_uri=None  # Will be set dynamically
)
scheduler = APScheduler()
cache = Cache()
cors = CORS()
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

# --- Redis client ---
redis_client = None

# --- Celery ---
celery = Celery(
    "pittstate_connect",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='US/Central',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000
)

# --- Flask-Login Configuration ---
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    """Delayed import to avoid circular import with models."""
    try:
        from models import User
        return User.query.get(int(user_id))
    except Exception as e:
        logging.error(f"❌ Error loading user: {e}")
        return None

# --- Initialization helper ---
def init_extensions(app):
    """Initialize all core extensions for the app."""
    global redis_client
    
    # Core database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Email
    mail.init_app(app)
    
    # Authentication
    login_manager.init_app(app)
    
    # Rate limiting with Redis if available
    if app.config.get('REDIS_URL'):
        limiter.storage_uri = app.config['REDIS_URL']
        logging.info("✅ Limiter configured with Redis storage")
    else:
        logging.warning("⚠️ Limiter using in-memory storage (not recommended for production)")
    limiter.init_app(app)
    
    # Caching
    cache.init_app(app, config={
        'CACHE_TYPE': 'redis' if app.config.get('REDIS_URL') else 'simple',
        'CACHE_REDIS_URL': app.config.get('REDIS_URL'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
    })
    
    # CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['*']),
            "methods": app.config.get('CORS_METHODS', ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
            "allow_headers": app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization'])
        }
    })
    
    # WebSocket
    socketio.init_app(app)
    
    # Redis client
    if app.config.get('REDIS_URL'):
        try:
            redis_client = Redis.from_url(app.config['REDIS_URL'], decode_responses=True)
            redis_client.ping()
            logging.info("✅ Redis connected successfully")
        except Exception as e:
            logging.warning(f"⚠️ Redis connection failed: {e}")
            redis_client = None
    
    # Celery
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # Scheduler
    scheduler.init_app(app)
    if not scheduler.running:
        try:
            scheduler.start()
            logging.info("✅ Scheduler started successfully")
        except Exception as e:
            logging.warning(f"⚠️ Scheduler start failed: {e}")
    
    # OAuth
    try:
        from services.oauth_service import init_oauth
        init_oauth(app)
        logging.info("✅ OAuth providers initialized")
    except Exception as e:
        logging.warning(f"⚠️ OAuth initialization failed: {e}")
    
    logging.info("✅ All extensions initialized successfully.")

