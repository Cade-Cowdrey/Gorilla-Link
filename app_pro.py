# =============================================================
# FILE: app_pro.py
# PittState-Connect — Main Application Factory
# Advanced production-ready Flask app with full blueprint loading,
# compression, security headers, CORS, AI setup, and logging.
# =============================================================

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from flask_compress import Compress
from flask_talisman import Talisman
from dotenv import load_dotenv
from loguru import logger
import sentry_sdk

# -------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------
# GLOBAL EXTENSIONS
# -------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()


# -------------------------------------------------------------
# APP FACTORY
# -------------------------------------------------------------
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---------------------------
    # CORE CONFIGURATION
    # ---------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///pittstate_connect.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.edu")

    # ---------------------------
    # SECURITY HEADERS
    # ---------------------------
    Talisman(app, content_security_policy=None)
    Compress(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # ---------------------------
    # EXTENSIONS INIT
    # ---------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"

    # ---------------------------
    # BLUEPRINT REGISTRATION
    # ---------------------------
    from blueprints.core.routes import core_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.careers.routes import careers_bp
    from blueprints.departments.routes import departments_bp
    from blueprints.scholarships.routes import scholarships_bp
    from blueprints.mentors.routes import mentors_bp
    from blueprints.alumni.routes import alumni_bp
    from blueprints.analytics.routes import analytics_bp
    from blueprints.donor.routes import donor_bp
    from blueprints.emails.routes import emails_bp
    from blueprints.notifications.routes import notifications_bp

    app.register_blueprint(core_bp)  # Root = '/'
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(careers_bp, url_prefix="/careers")
    app.register_blueprint(departments_bp, url_prefix="/departments")
    app.register_blueprint(scholarships_bp, url_prefix="/scholarships")
    app.register_blueprint(mentors_bp, url_prefix="/mentors")
    app.register_blueprint(alumni_bp, url_prefix="/alumni")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(donor_bp, url_prefix="/donor")
    app.register_blueprint(emails_bp, url_prefix="/emails")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")

    # ---------------------------
    # DATABASE ENSURE / LOGGING
    # ---------------------------
    with app.app_context():
        db.create_all()
        app.logger.info("📦 Database tables ensured.")

    # ---------------------------
    # LOGGING CONFIG
    # ---------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.info("🚀 Booting PittState-Connect (env=%s)", os.getenv("FLASK_ENV", "production"))
    app.logger.info("Compression: enabled")
    app.logger.info("✅ Blueprints registered successfully")

    # ---------------------------
    # SENTRY (OPTIONAL ENHANCEMENT)
    # ---------------------------
    if os.getenv("SENTRY_DSN"):
        sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)
        app.logger.info("🛰️ Sentry monitoring enabled")

    return app


# -------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
