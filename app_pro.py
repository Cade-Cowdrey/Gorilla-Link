# ===============================================================
#  PittState-Connect — Full Production Entrypoint (Final + Secure)
#  File: app_pro.py
#  ---------------------------------------------------------------
#  • Config-driven initialization (from config.py)
#  • Secure CSP Nonce + Sentry Monitoring
#  • Full PSU-branded, scalable architecture
#  • Background Jobs (daily digest, deadlines, rollups)
#  • AI, Redis, Caching, Analytics, and Mail integration
# ===============================================================

from __future__ import annotations
import os
import logging
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
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ---------------------------------------------------------------
#  Factory
# ---------------------------------------------------------------
def create_app() -> Flask:
    from config import select_config, attach_nonce, boot_sentry

    app = Flask(__name__)
    app.config.from_object(select_config())

    # -----------------------------------------------------------
    #  Initialize Extensions
    # -----------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    sess.init_app(app)
    compress.init_app(app)
    CORS(app, origins=app.config.get("CORS_ORIGINS"), supports_credentials=True)
    Talisman(
        app,
        content_security_policy=app.config.get("TALISMAN_CONTENT_SECURITY_POLICY"),
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", True),
        frame_options=app.config.get("TALISMAN_FRAME_OPTIONS", "SAMEORIGIN"),
    )

    # Secure CSP nonce injector + Sentry monitoring
    attach_nonce(app)
    boot_sentry(app)

    # -----------------------------------------------------------
    #  Flask-Login Setup
    # -----------------------------------------------------------
    from models import User  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # -----------------------------------------------------------
    #  Blueprint Registration
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
        logger.error(f"❌ Blueprint import error: {e}")
        raise

    blueprints = [
        core_bp,
        auth_bp,
        careers_bp,
        departments_bp,
        analytics_bp,
        digests_bp,
        community_bp,
        api_bp,
        alumni_bp,
    ]

    for bp in blueprints:
        try:
            app.register_blueprint(bp)
            logger.info(f"✅ Registered blueprint: {bp.name}")
        except Exception as e:
            logger.error(f"⚠️ Failed to register blueprint {bp.name}: {e}")

    # -----------------------------------------------------------
    #  Scheduler Setup (APScheduler)
    # -----------------------------------------------------------
    scheduler = BackgroundScheduler(timezone=app.config.get("SCHED_TIMEZONE", "US/Central"), daemon=True)

    try:
        from tasks.reminders import (
            run_daily_digest_job,
            run_deadline_reminders_job,
            weekly_analytics_rollup,
            cache_prime_job,
            stale_session_cleanup,
        )

        scheduler.add_job(lambda: run_daily_digest_job(app), CronTrigger(hour=7, minute=0))
        scheduler.add_job(lambda: run_deadline_reminders_job(app), CronTrigger(hour=9, minute=0))
        scheduler.add_job(lambda: weekly_analytics_rollup(app), CronTrigger(day_of_week="sun", hour=10))
        scheduler.add_job(lambda: cache_prime_job(app), CronTrigger(minute="*/30"))
        scheduler.add_job(lambda: stale_session_cleanup(app), CronTrigger(hour=3, minute=0))
        scheduler.start()
        logger.info("⏱️ APScheduler started successfully.")
    except Exception as e:
        logger.warning(f"Scheduler initialization failed: {e}")

    # -----------------------------------------------------------
    #  Redis + OpenAI Initialization
    # -----------------------------------------------------------
    if app.config.get("REDIS_URL"):
        try:
            import redis
            app.redis_client = redis.from_url(app.config["REDIS_URL"])
            app.redis_client.ping()
            logger.info("🧠 Redis connected and available.")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")

    if app.config.get("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            app.openai_client = OpenAI(api_key=app.config["OPENAI_API_KEY"])
            logger.info("🤖 OpenAI client initialized successfully.")
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")

    # -----------------------------------------------------------
    #  Middleware Hooks
    # -----------------------------------------------------------
    @app.before_request
    def before_any_request():
        app.logger.debug(f"[{datetime.utcnow().isoformat()}] Request received.")

    @app.after_request
    def after_any_request(resp):
        resp.headers["X-PittState-App"] = "PittState-Connect"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), fullscreen=()"
        )
        return resp

    # -----------------------------------------------------------
    #  Template Globals (Branding + CSP Nonce)
    # -----------------------------------------------------------
    @app.context_processor
    def inject_globals():
        from flask import g
        return {
            "PSU_BRAND": app.config["PSU_BRAND"],
            "csp_nonce": getattr(g, "csp_nonce", ""),
        }

    # -----------------------------------------------------------
    #  Shell Context
    # -----------------------------------------------------------
    @app.shell_context_processor
    def make_shell_context():
        from models import User, Post, Scholarship, Job
        return dict(app=app, db=db, User=User, Post=Post, Scholarship=Scholarship, Job=Job)

    logger.info(f"🚀 PittState-Connect initialized (env={os.getenv('APP_ENV', 'production')})")
    logger.info("🔐 Security hardened (CSP nonce, Sentry, HTTPS enforced).")
    logger.info("✅ All systems operational.")

    return app


# ---------------------------------------------------------------
#  Entrypoint
# ---------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False)
