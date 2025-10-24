# ================================================================
#  PittState-Connect | Advanced Flask Application Factory
#  Full PSU-branded, production-ready version with enhancements
# ================================================================

import os
import logging
from datetime import timedelta
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from flask_mail import Mail
from flask_session import Session
from flask_compress import Compress
from flask_cors import CORS
from flask_talisman import Talisman
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# Import dynamic config selector
from config import select_config, attach_nonce, boot_sentry

# Initialize core extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
sess = Session()
compress = Compress()
scheduler = BackgroundScheduler()

# ------------------------------------------------
#  Factory: Create Flask App
# ------------------------------------------------
def create_app():
    app = Flask(__name__)
    app_config = select_config()
    app.config.from_object(app_config)
    logger.info(f"Loaded config: {app_config.__name__}")

    # ------------------------------------------------
    #  Security: CSP + HTTPS via Talisman
    # ------------------------------------------------
    csp = getattr(app_config, "TALISMAN_CONTENT_SECURITY_POLICY", {"default-src": "'self'"})
    talisman = Talisman(
        app,
        content_security_policy=csp,
        force_https=app_config.TALISMAN_FORCE_HTTPS,
        session_cookie_secure=app_config.SESSION_COOKIE_SECURE if hasattr(app_config, "SESSION_COOKIE_SECURE") else True,
    )
    app.after_request(attach_nonce)

    # ------------------------------------------------
    #  Extensions initialization
    # ------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    CORS(app)

    # ------------------------------------------------
    #  Logging setup
    # ------------------------------------------------
    log_level = app.config.get("LOG_LEVEL", "INFO")
    logging.basicConfig(level=log_level)
    logger.info("Logging configured for level: {}", log_level)

    # ------------------------------------------------
    #  Scheduler setup (Analytics snapshots, reminders, etc.)
    # ------------------------------------------------
    if app.config.get("SCHEDULER_API_ENABLED", True):
        scheduler.start()
        logger.info("Background scheduler started.")

    # ------------------------------------------------
    #  Flask-Login setup
    # ------------------------------------------------
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from models import User  # Ensure User model exists and uses UserMixin

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"User load failed: {e}")
            return None

    # ------------------------------------------------
    #  Blueprints Auto-Register
    # ------------------------------------------------
    from importlib import import_module

    blueprints = [
        "core",
        "auth",
        "analytics",
        "careers",
        "alumni",
        "departments",
        "emails",
        "campus",
        "badges",
        "admin",
    ]

    for bp in blueprints:
        try:
            mod = import_module(f"blueprints.{bp}.routes")
            blueprint_obj = getattr(mod, f"{bp}_bp", None)
            if blueprint_obj:
                app.register_blueprint(blueprint_obj)
                logger.info(f"✅ Registered blueprint: {bp}")
            else:
                logger.warning(f"⚠️  No blueprint object found in: {bp}")
        except Exception as e:
            logger.error(f"⚠️  Failed to register {bp}: {e}")

    # ------------------------------------------------
    #  AI Helper Integration (Essay / Smart Match)
    # ------------------------------------------------
    openai_key = app.config.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            logger.info("OpenAI API connected successfully.")
        except Exception as e:
            logger.warning(f"OpenAI setup skipped: {e}")

    # ------------------------------------------------
    #  Error Handling
    # ------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # ------------------------------------------------
    #  Home route fallback (temporary)
    # ------------------------------------------------
    @app.route("/")
    def index():
        return render_template("core/home.html")

    # ------------------------------------------------
    #  Final system hooks
    # ------------------------------------------------
    boot_sentry(app)
    app.permanent_session_lifetime = timedelta(hours=8)

    return app


# ------------------------------------------------
#  Entry point for Gunicorn
# ------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
