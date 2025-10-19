import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from flask_moment import Moment

# -------------------------------------------------------------
# 🧩 Extensions
# -------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
cache = Cache()
scheduler = APScheduler()
moment = Moment()


# -------------------------------------------------------------
# ⚙️ Application Factory
# -------------------------------------------------------------
def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --- Configuration ---
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.com"
    )

    # --- Logging ---
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # --- Initialize Extensions ---
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
    moment.init_app(app)
    scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()
    app.logger.info("✅ Scheduler started successfully.")

    # ---------------------------------------------------------
    # 🧍 Flask-Login Setup
    # ---------------------------------------------------------
    from models import User  # ✅ make sure your User model exists in models.py

    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login user loader: loads user by ID."""
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.warning(f"⚠️ Failed to load user {user_id}: {e}")
            return None

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    app.logger.info("✅ Flask-Login user_loader registered successfully.")

    # ---------------------------------------------------------
    # 🧠 Auto-Load All Blueprints
    # ---------------------------------------------------------
    from importlib import import_module

    blueprints = [
        "core", "admin", "analytics", "alumni", "auth", "badges", "career", "campus",
        "connections", "departments", "digests", "engagement", "events", "feed", "groups",
        "map", "marketing", "mentorship", "notifications", "opportunities", "portfolio",
        "profile", "students", "stories", "api"
    ]

    for bp_name in blueprints:
        try:
            module = import_module(f"blueprints.{bp_name}.routes")
            for attr in dir(module):
                if attr.endswith("_bp"):
                    bp = getattr(module, attr)
                    app.register_blueprint(bp)
                    app.logger.info(f"✅ Loaded blueprint package: {bp_name}")
                    break
            else:
                app.logger.warning(f"⚠️ Skipped blueprint {bp_name}: no *_bp found")
        except Exception as e:
            app.logger.warning(f"⚠️ Skipped blueprint {bp_name}: {e}")

    # ---------------------------------------------------------
    # 🧾 Health Check
    # ---------------------------------------------------------
    @app.route("/health")
    def health():
        return "✅ PittState-Connect running", 200

    app.logger.info("✅ Flask-Moment initialized successfully.")
    return app


# -------------------------------------------------------------
# 🧠 App Instance for Render / Gunicorn
# -------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
