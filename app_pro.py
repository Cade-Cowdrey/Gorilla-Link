# -----------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Flask Production App — PSU Branded (Render Compatible)
# -----------------------------------------------------

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from flask_cors import CORS
from flask_moment import Moment
import os
import logging

# -----------------------------------------------------
# Extensions
# -----------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cache = Cache()
moment = Moment()

# -----------------------------------------------------
# Scheduler (for digests, etc.)
# -----------------------------------------------------
scheduler = APScheduler()

# -----------------------------------------------------
# Limiter (Rate Limiting)
# -----------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "200 per hour"])

# -----------------------------------------------------
# Create Application Factory
# -----------------------------------------------------
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load environment config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost/pittstate_connect"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # -----------------------------------------------------
    # Initialize Extensions
    # -----------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    scheduler.init_app(app)
    CORS(app)
    moment.init_app(app)

    # -----------------------------------------------------
    # Logging
    # -----------------------------------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.info("✅ Extensions initialized successfully.")

    # -----------------------------------------------------
    # Register Blueprints (Core First)
    # -----------------------------------------------------
    try:
        from blueprints.core.routes import core_bp
        app.register_blueprint(core_bp, url_prefix="/")
        app.logger.info("✅ Loaded blueprint: core")
    except Exception as e:
        app.logger.error(f"⚠️ Failed to load blueprint core: {e}")

    blueprint_modules = [
        "admin",
        "analytics",
        "alumni",
        "auth",
        "badges",
        "career",
        "campus",
        "connections",
        "departments",
        "digests",
        "engagement",
        "events",
        "feed",
        "groups",
        "map",
        "marketing",
        "mentorship",
        "notifications",
        "opportunities",
        "portfolio",
        "profile",
        "students",
        "stories",
        "api",
    ]

    for bp_name in blueprint_modules:
        try:
            module = __import__(f"blueprints.{bp_name}.routes", fromlist=[f"{bp_name}_bp"])
            bp = getattr(module, f"{bp_name}_bp")
            app.register_blueprint(bp, url_prefix=f"/{bp_name}")
            app.logger.info(f"✅ Loaded blueprint package: {bp_name}")
        except Exception as e:
            app.logger.warning(f"⚠️ Skipped blueprint {bp_name}: {e}")

    # -----------------------------------------------------
    # Scheduler Start
    # -----------------------------------------------------
    try:
        scheduler.start()
        app.logger.info("✅ Scheduler started successfully.")
    except Exception as e:
        app.logger.warning(f"⚠️ Scheduler start skipped: {e}")

    # -----------------------------------------------------
    # Root Health Check
    # -----------------------------------------------------
    @app.route("/status")
    def status():
        return (
            "✅ PittState-Connect is live — blueprints loaded successfully.",
            200,
            {"Content-Type": "text/plain"},
        )

    return app


# -----------------------------------------------------
# Run App
# -----------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
