from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_cors import CORS
from flask_moment import Moment

# -------------------------------------------------
# 🧩 CORE EXTENSIONS INITIALIZATION
# -------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
moment = Moment()


# -------------------------------------------------
# 🔧 CONFIGURE EXTENSIONS FUNCTION
# -------------------------------------------------
def init_extensions(app):
    """Initialize all core Flask extensions for PittState-Connect."""
    # Database
    db.init_app(app)
    migrate.init_app(app, db)

    # Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Mail (PSU-branded)
    mail.init_app(app)

    # CORS for APIs / JSON endpoints
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Moment.js for event timestamps
    moment.init_app(app)

    # Confirm
    app.logger.info("✅ Flask extensions initialized successfully.")


# -------------------------------------------------
# 🔐 LOGIN MANAGER USER LOADER
# -------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Fetches a user from the database by ID for session management."""
    from models import User
    return User.query.get(int(user_id))
