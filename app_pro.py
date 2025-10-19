# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Application Factory — Production Entry Point
# ---------------------------------------------------------
import os
from flask import Flask
from config import get_config
from extensions import db, mail, migrate, login_manager, cache
from flask_cors import CORS
from flask_apscheduler import APScheduler

# ---------------------------------------------------------
# Application Factory
# ---------------------------------------------------------
def create_app():
    """Factory pattern to create and configure the Flask app."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(get_config())

    # Enable CORS
    CORS(app)

    # -----------------------------------------------------
    # Initialize Core Extensions
    # -----------------------------------------------------
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)

    # -----------------------------------------------------
    # APScheduler (for digests, cleanup, etc.)
    # -----------------------------------------------------
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # -----------------------------------------------------
    # Blueprint Registration
    # -----------------------------------------------------
    from blueprints import (
        admin,
        alumni,
        analytics,
        api,
        auth,
        badges,
        campus,
        career,
        connections,
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
    )

    blueprint_packages = [
        admin,
        alumni,
        analytics,
        api,
        auth,
        badges,
        campus,
        career,
        connections,
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
    ]

    for package in blueprint_packages:
        try:
            # Each blueprint file defines a *_bp variable (e.g., admin_bp)
            for attr_name in dir(package):
                if attr_name.endswith("_bp"):
                    bp = getattr(package, attr_name)
                    app.register_blueprint(bp)
                    print(f"✅ Loaded blueprint package: {package.__name__}")
                    break
        except Exception as e:
            print(f"⚠️  Skipped blueprint {package.__name__}: {e}")

    # -----------------------------------------------------
    # CLI + Shell Context
    # -----------------------------------------------------
    @app.shell_context_processor
    def make_shell_context():
        from models import User, Department, Post, Event, AuditLog
        return {
            "db": db,
            "User": User,
            "Department": Department,
            "Post": Post,
            "Event": Event,
            "AuditLog": AuditLog,
        }

    # -----------------------------------------------------
    # Index Route (Fallback)
    # -----------------------------------------------------
    @app.route("/")
    def index():
        return "<h1>🦍 PittState-Connect is live!</h1><p>Blueprints loaded successfully.</p>"

    return app


# ---------------------------------------------------------
# Entry Point for Render / Gunicorn
# ---------------------------------------------------------
app = create_app()

# ---------------------------------------------------------
# Run Locally (optional)
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
