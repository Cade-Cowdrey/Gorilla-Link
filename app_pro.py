# ================================================================
#  PittState-Connect | Advanced Flask Application Factory
#  PSU-branded | Secure | Analytics & AI Enabled
# ================================================================

import os
import logging
from datetime import timedelta
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask_compress import Compress
from flask_cors import CORS
from flask_talisman import Talisman
from apscheduler.schedulers.background import BackgroundScheduler
from flask_caching import Cache
from loguru import logger

from config import select_config, attach_nonce, boot_sentry

# ------------------------------------------------
#  Extension Instances
# ------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
sess = Session()
compress = Compress()
scheduler = BackgroundScheduler()
cache = Cache()

# ------------------------------------------------
#  Factory: Create App
# ------------------------------------------------
def create_app():
    app = Flask(__name__)
    app_config = select_config()
    app.config.from_object(app_config)
    logger.info(f"Loaded config: {app_config.__name__}")

    # --- Security / HTTPS ---
    csp = getattr(app_config, "TALISMAN_CONTENT_SECURITY_POLICY", {"default-src": "'self'"})
    Talisman(app, content_security_policy=csp, force_https=True)
    app.after_request(attach_nonce)

    # --- Core Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    CORS(app)
    cache.init_app(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

    # --- Logging ---
    logging.basicConfig(level=app.config.get("LOG_LEVEL", "INFO"))
    logger.info("Logging configured successfully.")

    # --- Scheduler ---
    if app.config.get("SCHEDULER_API_ENABLED", True):
        scheduler.start()
        logger.info("Background scheduler started.")

    # --- Flask-Login ---
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"User load failed: {e}")
            return None

    # --- Blueprints ---
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
            bp_obj = getattr(mod, f"{bp}_bp", None)
            if bp_obj:
                app.register_blueprint(bp_obj)
                logger.info(f"✅ Registered blueprint: {bp}")
            else:
                logger.warning(f"⚠️  No blueprint found for {bp}")
        except Exception as e:
            logger.error(f"⚠️  Failed to register {bp}: {e}")

    # --- AI / OpenAI Integration ---
    openai_key = app.config.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            logger.info("OpenAI API connected successfully.")
        except Exception as e:
            logger.warning(f"OpenAI setup skipped: {e}")

    # --- Error Pages ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.route("/")
    def index():
        return render_template("core/home.html")

    # --- Final System Hooks ---
    boot_sentry(app)
    app.permanent_session_lifetime = timedelta(hours=8)
    return app


# ------------------------------------------------
#  Gunicorn Entry
# ------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
