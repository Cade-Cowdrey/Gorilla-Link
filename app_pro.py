# app_pro.py
# ===============================================================
#  PittState-Connect | PSU-Branded Full Production App (Final)
#  ---------------------------------------------------------------
#  Includes:
#   - Unified blueprint registration
#   - AI Tools, Digests, Donor, Employer, Security, Analytics
#   - Flask-Login + SQLAlchemy + Mail setup
#   - APScheduler for automated reminders
#   - CORS, Compression, Talisman (security), DebugToolbar
# ===============================================================

from __future__ import annotations
import os, logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_compress import Compress
from flask_cors import CORS
from flask_session import Session
from flask_talisman import Talisman
from flask_debugtoolbar import DebugToolbarExtension
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize core extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
compress = Compress()
toolbar = DebugToolbarExtension()


# ===============================================================
#  App Factory
# ===============================================================
def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # ------------------------------------------------------------
    #  Configuration
    # ------------------------------------------------------------
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///pittstate.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        SESSION_TYPE="filesystem",
        SESSION_PERMANENT=False,
        DEBUG_TB_INTERCEPT_REDIRECTS=False,
    )

    # ------------------------------------------------------------
    #  Extensions Initialization
    # ------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    compress.init_app(app)
    Session(app)
    CORS(app)
    toolbar.init_app(app)
    Talisman(app, content_security_policy=None)

    # ------------------------------------------------------------
    #  User loader for Flask-Login
    # ------------------------------------------------------------
    from models import User  # Ensure your User model exists

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # ------------------------------------------------------------
    #  Register Blueprints
    # ------------------------------------------------------------
    from blueprints.core.routes import core_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.digests import digests_bp
    from blueprints.ai_tools import ai_tools_bp
    from blueprints.donor import donor_bp
    from blueprints.employer import employer_bp
    from blueprints.security import security_bp
    from blueprints.api.routes import api_bp
    from blueprints.analytics.routes import analytics_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(digests_bp)
    app.register_blueprint(ai_tools_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analytics_bp)

    app.logger.info("✅ Blueprints registered successfully")

    # ------------------------------------------------------------
    #  Scheduler Setup (for Digests + Deadlines)
    # ------------------------------------------------------------
    try:
        from tasks.reminders import run_daily_digest_job, run_deadline_reminders_job

        scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
        scheduler.add_job(lambda: run_daily_digest_job(app), "cron", hour=12, minute=0)
        scheduler.add_job(lambda: run_deadline_reminders_job(app), "cron", hour=13, minute=0)

        # Only start on one dyno in production
        if os.getenv("SCHEDULER_LEADER", "1") == "1":
            scheduler.start()
            app.logger.info("🕒 Scheduler started successfully")
    except Exception as e:
        app.logger.error(f"⚠️ Scheduler init failed: {e}")

    # ------------------------------------------------------------
    #  Logging
    # ------------------------------------------------------------
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    app.logger.info("🚀 Booting PittState-Connect (env=%s)", os.getenv("FLASK_ENV", "production"))
    app.logger.info("Compression: enabled")

    return app


# ===============================================================
#  App Entry Point
# ===============================================================
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
