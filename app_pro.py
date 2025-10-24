# ===============================================================
#  PittState-Connect — Production Application Entrypoint
#  File: app_pro.py
#  ---------------------------------------------------------------
#  Full enterprise-grade configuration:
#   • Flask + SQLAlchemy + Migrate
#   • Flask-Login + Session + Mail + APScheduler
#   • Blueprint Auto-Loader
#   • Secure headers (Flask-Talisman)
#   • Compression, CORS, Redis-aware caching
#   • Background tasks (Daily Digest, Deadlines, Rollup, etc.)
# ===============================================================

from __future__ import annotations
import os, logging, sys, json
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask_cors import CORS
from flask_compress import Compress
from flask_talisman import Talisman
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# ---------------------------------------------------------------
#  Core Extensions
# ---------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
sess = Session()
compress = Compress()

# ---------------------------------------------------------------
#  Logging Setup
# ---------------------------------------------------------------
LOG_PATH = "logs"
os.makedirs(LOG_PATH, exist_ok=True)
logger.add(f"{LOG_PATH}/app.log", rotation="5 MB", retention="7 days", level="INFO", enqueue=True)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ---------------------------------------------------------------
#  Factory
# ---------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__)

    # -----------------------------------------------------------
    #  Configuration
    # -----------------------------------------------------------
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///pittstate_connect.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.edu"),
        SESSION_TYPE="filesystem",
        SESSION_PERMANENT=False,
        COMPRESS_ALGORITHM="br",
        COMPRESS_LEVEL=6,
        TEMPLATES_AUTO_RELOAD=True,
        JSON_SORT_KEYS=False,
    )

    # -----------------------------------------------------------
    #  Initialize Extensions
    # -----------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    CORS(app, supports_credentials=True)
    Talisman(app, content_security_policy=None)

    # -----------------------------------------------------------
    #  Flask-Login Setup
    # -----------------------------------------------------------
    from models import User  # noqa
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    login_manager.login_view = "auth_bp.login"

    # -----------------------------------------------------------
    #  Blueprints Auto-Registration
    # -----------------------------------------------------------
    try:
        from blueprints.core.routes import core_bp
        from blueprints.auth.routes import auth_bp
        from blueprints.careers.routes import careers_bp
        from blueprints.departments.routes import departments_bp
        from blueprints.analytics.routes import analytics_bp
        from blueprints.digests.routes import digests_bp
        from blueprints.community.routes import community_bp
        from blueprints.api.routes import api_bp
        from blueprints.alumni.routes import alumni_bp
    except Exception as e:
        logger.error(f"Blueprint import error: {e}")
        raise

    blueprints = [
        core_bp, auth_bp, careers_bp, departments_bp,
        analytics_bp, digests_bp, community_bp, api_bp, alumni_bp,
    ]

    for bp in blueprints:
        try:
            app.register_blueprint(bp)
        except Exception as e:
            logger.error(f"Failed to register blueprint {bp.name}: {e}")

    logger.info("✅ Blueprints registered successfully")

    # -----------------------------------------------------------
    #  Scheduler Setup
    # -----------------------------------------------------------
    scheduler = BackgroundScheduler(timezone="US/Central", daemon=True)

    try:
        from tasks.reminders import (
            run_daily_digest_job,
            run_deadline_reminders_job,
            weekly_analytics_rollup,
            cache_prime_job,
            stale_session_cleanup,
        )
    except Exception as e:
        logger.warning(f"Scheduler import failed: {e}")
        run_daily_digest_job = run_deadline_reminders_job = lambda app: None
        weekly_analytics_rollup = cache_prime_job = stale_session_cleanup = lambda app: None

    # Schedule recurring jobs
    scheduler.add_job(lambda: run_daily_digest_job(app), CronTrigger(hour=7, minute=0))
    scheduler.add_job(lambda: run_deadline_reminders_job(app), CronTrigger(hour=9, minute=0))
    scheduler.add_job(lambda: weekly_analytics_rollup(app), CronTrigger(day_of_week="sun", hour=10, minute=0))
    scheduler.add_job(lambda: cache_prime_job(app), CronTrigger(minute="*/30"))
    scheduler.add_job(lambda: stale_session_cleanup(app), CronTrigger(hour=3, minute=0))

    try:
        scheduler.start()
        logger.info("⏱️  APScheduler started successfully")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")

    # -----------------------------------------------------------
    #  Startup Hooks
    # -----------------------------------------------------------
    @app.before_request
    def before_any_request():
        app.logger.debug(f"[{datetime.utcnow().isoformat()}] Incoming: {getattr(app, 'request_class', 'GET')}")

    @app.after_request
    def after_any_request(resp):
        resp.headers["X-PittState-App"] = "PittState-Connect"
        return resp

    @app.shell_context_processor
    def make_shell_context():
        from models import User, Post, Scholarship, Job
        return {"db": db, "User": User, "Post": Post, "Scholarship": Scholarship, "Job": Job}

    # -----------------------------------------------------------
    #  OpenAI Health Check (optional)
    # -----------------------------------------------------------
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("🤖 OpenAI client initialized successfully")
            setattr(app, "openai_client", client)
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    # -----------------------------------------------------------
    #  Cache & Redis Warmup
    # -----------------------------------------------------------
    if os.getenv("REDIS_URL"):
        try:
            import redis
            r = redis.from_url(os.getenv("REDIS_URL"))
            r.ping()
            setattr(app, "redis_client", r)
            logger.info("🧠 Redis connected and available")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")

    # -----------------------------------------------------------
    #  Security Headers & Branding
    # -----------------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": {
                "name": "PittState-Connect",
                "tagline": "Connecting Gorillas for Life 🦍",
                "crimson": "#A6192E",
                "gold": "#FFB81C",
            }
        }

    logger.info(f"🚀 Booting PittState-Connect (env={os.getenv('RENDER_ENV', 'production')})")
    logger.info("Compression: enabled")

    return app


# ===============================================================
#  App Instance (Gunicorn Entry)
# ===============================================================
app = create_app()

# ===============================================================
#  Gunicorn Entrypoint
# ===============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False)
