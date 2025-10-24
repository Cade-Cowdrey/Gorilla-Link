# ================================================================
#  PittState-Connect | Advanced Flask Application Factory
#  PSU-branded | Secure | AI & Analytics Enabled | Production-Ready
# ================================================================

import os
import logging
from datetime import timedelta
from importlib import import_module

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask_compress import Compress
from flask_cors import CORS
from flask_talisman import Talisman
from flask_caching import Cache
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# --- Config Selectors ---
from config import select_config, attach_nonce, boot_sentry

# ------------------------------------------------
#  Global Extensions
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

    # ------------------------------------------------
    #  Security: HTTPS + CSP + Nonce
    # ------------------------------------------------
    csp = getattr(
        app_config,
        "TALISMAN_CONTENT_SECURITY_POLICY",
        {
            "default-src": "'self'",
            "img-src": ["'self'", "data:", "https://*"],
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'"],
        },
    )
    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        session_cookie_secure=True,
    )
    app.after_request(attach_nonce)

    # ------------------------------------------------
    #  Extensions Initialization
    # ------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})
    CORS(app, resources={r"/*": {"origins": "*"}})

    # ------------------------------------------------
    #  Logging
    # ------------------------------------------------
    logging.basicConfig(level=app.config.get("LOG_LEVEL", "INFO"))
    logger.info("Logging configured successfully.")

    # ------------------------------------------------
    #  Background Scheduler
    # ------------------------------------------------
    if app.config.get("SCHEDULER_API_ENABLED", True):
        scheduler.start()
        logger.info("Background scheduler started.")

    # ------------------------------------------------
    #  Flask-Login Setup
    # ------------------------------------------------
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

    # ------------------------------------------------
    #  Register Blueprints Automatically
    # ------------------------------------------------
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
                logger.warning(f"⚠️  No blueprint object found in: {bp}")
        except Exception as e:
            logger.error(f"⚠️  Failed to register {bp}: {e}")

    # ------------------------------------------------
    #  AI / OpenAI Integration
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
    #  PSU Branding (Global Jinja Context)
    # ------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": {
                "crimson": "#A6192E",
                "gold": "#FFB81C",
                "gray": "#5A5A5A",
                "white": "#FFFFFF",
                "black": "#000000",
                "accent": "#D7A22A",
                "gradient": "linear-gradient(90deg, #A6192E 0%, #FFB81C 100%)",
                "tagline": "PittState-Connect — Linking Gorillas for Life",
                "favicon": "/static/images/psu_logo.png",
            },
            "APP_VERSION": "2.0-Final",
            "APP_ENV": app.config.get("FLASK_ENV", "production").capitalize(),
        }

    # ------------------------------------------------
    #  Health Check Endpoint
    # ------------------------------------------------
    @app.route("/health")
    def health():
        return {"status": "ok", "uptime": "active", "env": app.config.get("FLASK_ENV")}, 200

    # ------------------------------------------------
    #  Error Handlers
    # ------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # ------------------------------------------------
    #  Root Route (Fallback)
    # ------------------------------------------------
    @app.route("/")
    def index():
        logger.info(f"Visitor from {request.remote_addr}")
        return render_template("core/home.html")

    # ------------------------------------------------
    #  Boot Integrations
    # ------------------------------------------------
    boot_sentry(app)
    app.permanent_session_lifetime = timedelta(hours=8)

    return app


# ------------------------------------------------
#  Entry Point for Gunicorn
# ------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
