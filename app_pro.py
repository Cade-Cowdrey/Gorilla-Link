# ================================================================
#  PittState-Connect | Advanced Flask Application Factory
#  PSU-branded · Secure · AI-Ready · Analytics-Driven · Production-Optimized
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

# --- Config helpers ---
from config import select_config, attach_nonce, boot_sentry

# ------------------------------------------------
#  Global Flask extensions
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
#  App Factory
# ------------------------------------------------
def create_app():
    app = Flask(__name__)

    # ------------------------------------------------
    #  Load environment config
    # ------------------------------------------------
    app_config = select_config()
    app.config.from_object(app_config)
    logger.info(f"Loaded config: {app_config.__name__}")

    # ------------------------------------------------
    #  Security middleware (Talisman + CSP nonce)
    # ------------------------------------------------
    csp = app_config.TALISMAN_CONTENT_SECURITY_POLICY
    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        session_cookie_secure=True,
        content_security_policy_nonce_in=["script-src"],
    )
    app.after_request(attach_nonce)

    # ------------------------------------------------
    #  Initialize extensions
    # ------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": app.config.get("CACHE_TYPE", "SimpleCache")})
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # ------------------------------------------------
    #  Logging configuration (case-safe fix)
    # ------------------------------------------------
    log_level = app.config.get("LOG_LEVEL", "INFO")
    if isinstance(log_level, str):
        log_level = log_level.upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    logger.info("Logging configured successfully.")

    # ------------------------------------------------
    #  Scheduler
    # ------------------------------------------------
    if app.config.get("SCHEDULER_API_ENABLED", True):
        scheduler.start()
        logger.info("Background scheduler started.")

    # ------------------------------------------------
    #  Flask-Login setup
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
    #  Auto-register blueprints
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
        "api",  # ✅ new API layer
        "donor",
        "scholarships",
        "mentors",
        "notifications",
    ]

    for bp in blueprints:
        try:
            mod = import_module(f"blueprints.{bp}.routes")
            bp_obj = getattr(mod, f"{bp}_bp", None)
            if bp_obj:
                app.register_blueprint(bp_obj)
                logger.info(f"✅ Registered blueprint: {bp}")
            else:
                logger.warning(f"⚠️ No blueprint object found in {bp}")
        except Exception as e:
            logger.error(f"❌ Failed to register {bp}: {e}")

    # ------------------------------------------------
    #  AI Integration (OpenAI)
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
    #  Redis integration
    # ------------------------------------------------
    redis_url = app.config.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            app.redis_client = redis.from_url(redis_url)
            logger.info("✅ Redis connected successfully.")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            app.redis_client = None
    else:
        app.redis_client = None

    # ------------------------------------------------
    #  PSU Branding (Jinja context)
    # ------------------------------------------------
    @app.context_processor
    def inject_globals():
        brand = app.config.get("PSU_BRAND", {}) or {
            "crimson": "#A6192E",
            "gold": "#FFB81C",
            "gray": "#5A5A5A",
            "white": "#FFFFFF",
            "black": "#000000",
            "accent": "#D7A22A",
            "gradient": "linear-gradient(90deg, #A6192E 0%, #FFB81C 100%)",
            "tagline": "PittState-Connect — Linking Gorillas for Life",
            "favicon": "/static/images/psu_logo.png",
        }
        return {
            "PSU_BRAND": brand,
            "APP_VERSION": "2.0-Final",
            "APP_ENV": app.config.get("FLASK_ENV", "production").capitalize(),
        }

    # ------------------------------------------------
    #  Analytics auto-update job
    # ------------------------------------------------
    def collect_usage_metrics():
        """Example scheduled analytics aggregation job."""
        try:
            from models import User
            total = db.session.query(User).count()
            cache.set("analytics:total_users", total, timeout=3600)
            logger.info(f"[Scheduler] Cached total users: {total}")
        except Exception as e:
            logger.warning(f"[Scheduler] Analytics job failed: {e}")

    scheduler.add_job(collect_usage_metrics, "interval", hours=1, id="analytics_job", replace_existing=True)

    # ------------------------------------------------
    #  Health & system routes
    # ------------------------------------------------
    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "redis": bool(app.redis_client),
            "ai_enabled": bool(openai_key),
            "env": app.config.get("FLASK_ENV"),
            "version": "2.0-Final",
        }, 200

    @app.route("/")
    def index():
        logger.info(f"Visitor from {request.remote_addr}")
        return render_template("core/home.html")

    # ------------------------------------------------
    #  Error handlers
    # ------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # ------------------------------------------------
    #  Boot sentry & finalize
    # ------------------------------------------------
    boot_sentry(app)
    app.permanent_session_lifetime = timedelta(hours=8)

    return app


# ------------------------------------------------
#  Gunicorn entry point
# ------------------------------------------------
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
