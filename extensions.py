# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Flask Extensions Initialization
# ---------------------------------------------------------
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
cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})


# ---------------------------------------------------------
# Flask-Login Configuration
# ---------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
