# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
migrate = Migrate()
socketio = SocketIO(async_mode="threading")  # eventlet is installed; switch if desired
