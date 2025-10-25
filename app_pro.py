import os
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template, request, g
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from redis import Redis
from openai import OpenAI
from config import select_config, attach_nonce, boot_sentry

# ------------------------------------------------------
# App-level globals
# ------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
scheduler = BackgroundScheduler(timezone="UTC")

redis_client = None
openai_client = None


# ------------------------------------------------------
# Factory pattern
# ------------------------------------------------------
def create_app():
    app = Flask(__name__)
    config_class = select_config()
    app.config.from_object(config_class)

    # Core extensions
    CORS(app)
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Logging setup
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    app.logger.info(f"Loaded config: {config_class.__name__}")
    app.logger.info("Logging configured successfully.")

    # Sentry initialization
    boot_sentry(app)

    # Security nonce
    @app.before_request
    def add_nonce():
        attach_nonce(app)

    # Redis + OpenAI
    global redis_client, openai_client
    try:
        redis_client = Redis.from_url(app.config.get("REDIS_URL"))
        app.logger.info("✅ Redis connected successfully.")
    except Exception as e:
        app.logger.warning(f"⚠️ Redis unavailable: {e}")

    try:
        openai_client = OpenAI(api_key=app.config.get("OPENAI_API_KEY"))
        app.logger.info("✅ OpenAI API connected successfully.")
    except Exception as e:
        app.logger.warning(f"⚠️ OpenAI unavailable: {e}")

    # ------------------------------------------------------
    # Blueprints registration (auto)
    # ------------------------------------------------------
    from blueprints import (
        core_bp, auth_bp, analytics_bp, careers_bp, alumni_bp, departments_bp,
        emails_bp, campus_bp, badges_bp, admin_bp, api_bp,
        donor_bp, scholarships_bp, mentors_bp, notifications_bp
    )

    blueprints = [
        core_bp, auth_bp, analytics_bp, careers_bp, alumni_bp,
        departments_bp, emails_bp, campus_bp, badges_bp, admin_bp,
        api_bp, donor_bp, scholarships_bp, mentors_bp, notifications_bp
    ]
    for bp in blueprints:
        app.register_blueprint(bp)
        app.logger.info(f"✅ Registered blueprint: {bp.name}")

    # ------------------------------------------------------
    # Context processors (global template vars)
    # ------------------------------------------------------
    @app.context_processor
    def inject_globals():
        return dict(
            PSU_BRAND={
                "favicon": "/static/img/psu_logo.png",
                "gradient": "linear-gradient(90deg, #990000, #FFC72C)",
                "tagline": "Once a Gorilla, Always a Gorilla."
            },
            GOOGLE_ANALYTICS_ID=app.config.get("GOOGLE_ANALYTICS_ID", "G-XXXXXXX"),
            now=datetime.utcnow
        )

    # ------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Error: {request.path}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 Error: {e}")
        return render_template("errors/500.html"), 500

    # ------------------------------------------------------
    # Background jobs (with safe context)
    # ------------------------------------------------------
    from utils.analytics_util import run_usage_analytics

    def collect_usage_metrics():
        """Safely collect app analytics inside proper context."""
        with app.app_context():
            try:
                data = run_usage_analytics(db)
                app.logger.info(f"[Scheduler] Analytics updated: {data}")
            except Exception as e:
                app.logger.warning(f"[Scheduler] Analytics job failed: {e}")

    # Start scheduler
    scheduler.add_job(func=collect_usage_metrics, trigger="interval", hours=1)
    scheduler.start()
    app.logger.info("Background scheduler started.")

    # ------------------------------------------------------
    # Health endpoint
    # ------------------------------------------------------
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

    return app


# ------------------------------------------------------
# Run directly
# ------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
