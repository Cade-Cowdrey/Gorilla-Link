# ============================================================
# FILE: app_pro.py
# Main Flask application factory for PittState-Connect
# ============================================================

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

# ============================================================
# Initialize core extensions
# ============================================================
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()


# ============================================================
# Application Factory
# ============================================================
def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # --------------------------------------------------------
    # Dynamic Config (Development vs Production)
    # --------------------------------------------------------
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        app.config.from_object("config.config_dev.DevConfig")
    else:
        app.config.from_object("config.Config")

    # --------------------------------------------------------
    # Initialize Extensions
    # --------------------------------------------------------
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # --------------------------------------------------------
    # Login Manager setup
    # --------------------------------------------------------
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # --------------------------------------------------------
    # Register Blueprints (auto-discovery)
    # --------------------------------------------------------
    from blueprints import (
        admin_bp,
        alumni_bp,
        analytics_bp,
        auth_bp,
        careers_bp,
        core_bp,
        departments_bp,
        donor_bp,
        emails_bp,
        scholarships_bp,
    )

    blueprints = [
        core_bp,
        auth_bp,
        admin_bp,
        alumni_bp,
        analytics_bp,
        careers_bp,
        departments_bp,
        donor_bp,
        emails_bp,
        scholarships_bp,
    ]

    for bp in blueprints:
        try:
            app.register_blueprint(bp)
            print(f"✅ Registered blueprint: {bp.name} ({bp.url_prefix or 'root'})")
        except Exception as e:
            print(f"⚠️  Failed to register {bp.name}: {e}")

    print("✅ All blueprints registered successfully.\n")

    # --------------------------------------------------------
    # Database Models import (avoids circular imports)
    # --------------------------------------------------------
    with app.app_context():
        import models

        db.create_all()

    # --------------------------------------------------------
    # Security Headers
    # --------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # --------------------------------------------------------
    # PSU Themed Welcome Banner
    # --------------------------------------------------------
    print(
        f"""
    🦍  PittState-Connect started successfully!
    Environment: {env.upper()}
    Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}
    Debug: {app.config.get('DEBUG')}
    ----------------------------------------------------------
    """
    )

    return app


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    app = create_app()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
