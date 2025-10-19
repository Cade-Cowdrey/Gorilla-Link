# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Application Factory (Production Entrypoint)
# ---------------------------------------------------------
import os
from flask import Flask
from extensions import db, mail, migrate, login_manager, cache
from utils.mail_util import send_email

# ---------------------------------------------------------
# Factory Function
# ---------------------------------------------------------
def create_app():
    app = Flask(__name__)

    # -----------------------------------------------------
    # Configuration
    # -----------------------------------------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")

    # Mail Configuration
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@pittstateconnect.edu"
    )

    # -----------------------------------------------------
    # Initialize Extensions
    # -----------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)

    # -----------------------------------------------------
    # Import Models (register for migrations)
    # -----------------------------------------------------
    from models import (
        User,
        Department,
        Post,
        Comment,
        Event,
        Notification,
        Badge,
        AuditLog,
    )

    # -----------------------------------------------------
    # Register Blueprints
    # -----------------------------------------------------
    from blueprints import (
        admin,
        alumni,
        analytics,
        auth,
        badges,
        campus,
        career,
        careers,
        core,
        departments,
        digests,
        engagement,
        events,
        feed,
        groups,
        map,
        marketing,
        mentorship,
        notifications,
        opportunities,
        portfolio,
        profile,
        stories,
        students,
        connections,
    )

    blueprints = [
        admin,
        alumni,
        analytics,
        auth,
        badges,
        campus,
        career,
        careers,
        core,
        departments,
        digests,
        engagement,
        events,
        feed,
        groups,
        map,
        marketing,
        mentorship,
        notifications,
        opportunities,
        portfolio,
        profile,
        stories,
        students,
        connections,
    ]

    for bp in blueprints:
        try:
            app.register_blueprint(bp.routes.__getattribute__(f"{bp.__name__}_bp"))
            print(f"✅ Loaded blueprint package: {bp.__name__}")
        except Exception as e:
            print(f"⚠️  Skipped blueprint {bp.__name__}: {e}")

    # -----------------------------------------------------
    # Root Route
    # -----------------------------------------------------
    @app.route("/")
    def index():
        return "<h2>🦍 PittState-Connect is running successfully on Render!</h2>"

    return app


# ---------------------------------------------------------
# Gunicorn Entrypoint
# ---------------------------------------------------------
app = create_app()
