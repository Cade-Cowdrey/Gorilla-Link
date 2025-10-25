import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from dotenv import load_dotenv

# -----------------------------------------------------------
# Load environment and initialize extensions
# -----------------------------------------------------------
load_dotenv()
db = SQLAlchemy()
mail = Mail()
redis_client = None

# -----------------------------------------------------------
# Configuration
# -----------------------------------------------------------
class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "psu_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_DEFAULT_SENDER = ("PittState Connect", "noreply@pittstate.edu")
    MAIL_USE_TLS = True
    MAIL_PORT = 587
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")
    PSU_BRAND = {
        "crimson": "#990000",
        "gold": "#FFCC00",
        "gradient": "linear-gradient(90deg, #990000, #FFCC00)",
        "tagline": "Gorillas Lead the Way",
        "favicon": "/static/img/psu_logo.png"
    }

class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")

class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///prod.db")

def select_config():
    env = os.getenv("FLASK_ENV", "production").lower()
    print(f"[config] Using configuration for environment: {env}")
    return DevConfig if env == "development" else ProdConfig

# -----------------------------------------------------------
# App Factory
# -----------------------------------------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(select_config())

    # -------------------------------------------------------
    # Logging Setup
    # -------------------------------------------------------
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging configured successfully.")

    # -------------------------------------------------------
    # Initialize Core Extensions
    # -------------------------------------------------------
    CORS(app)
    db.init_app(app)
    mail.init_app(app)

    limiter = Limiter(
        get_remote_address,
        app=app,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
        default_limits=["100 per minute"]
    )

    # -------------------------------------------------------
    # Redis Connection
    # -------------------------------------------------------
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        app.logger.info("✅ Redis connected successfully.")
    except Exception as e:
        redis_client = None
        app.logger.warning(f"⚠️ Redis unavailable: {e}")
    app.extensions["redis"] = redis_client

    # -------------------------------------------------------
    # Initialize Scheduler (centralized)
    # -------------------------------------------------------
    from utils.scheduler import init_scheduler
    init_scheduler(app)
    app.logger.info("✅ Background scheduler initialized via utils.scheduler.")

    # -------------------------------------------------------
    # Flask-Login Setup
    # -------------------------------------------------------
    from models import User  # ensure this imports your user model
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # Standard user loader (for session cookies)
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.warning(f"⚠️ user_loader failed for user_id {user_id}: {e}")
            return None

    # Optional API token loader (for Authorization Bearer)
    @login_manager.request_loader
    def load_user_from_request(req: request):
        token = req.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            from models import UserToken  # optional model if using API tokens
            token_str = token[7:]
            try:
                user_token = UserToken.verify_token(token_str)
                if user_token:
                    app.logger.info(f"✅ Authenticated API user via token {token_str[:6]}...")
                    return user_token.user
            except Exception as e:
                app.logger.warning(f"⚠️ Token validation failed: {e}")
        return None

    # -------------------------------------------------------
    # Sentry Integration (optional)
    # -------------------------------------------------------
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()])
            app.logger.info("✅ Sentry initialized.")
        except Exception as e:
            app.logger.warning(f"Sentry init failed: {e}")
    else:
        app.logger.info("Sentry DSN not found — skipping initialization.")

    # -------------------------------------------------------
    # PSU Branding Globals
    # -------------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": app.config["PSU_BRAND"],
            "GOOGLE_ANALYTICS_ID": os.getenv("GOOGLE_ANALYTICS_ID", ""),
            "now": datetime.utcnow
        }

    # -------------------------------------------------------
    # Blueprint Registration
    # -------------------------------------------------------
    with app.app_context():
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

        blueprints = [
            core_bp, auth_bp, careers_bp, departments_bp,
            scholarships_bp, mentors_bp, alumni_bp,
            analytics_bp, donor_bp, emails_bp, notifications_bp
        ]

        for bp in blueprints:
            try:
                app.register_blueprint(bp)
                app.logger.info(f"✅ Registered blueprint: {bp.name}")
            except Exception as e:
                app.logger.warning(f"⚠️ Failed to register blueprint {bp.name}: {e}")

    # -------------------------------------------------------
    # OpenAI API Verification
    # -------------------------------------------------------
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            app.logger.info("✅ OpenAI API key verified.")
        except Exception as e:
            app.logger.warning(f"⚠️ OpenAI key verification failed: {e}")

    # -------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server Error: %s", e)
        return render_template("errors/500.html"), 500

    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "environment": os.getenv("FLASK_ENV", "production"),
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    return app


# -----------------------------------------------------------
# Entrypoint for Gunicorn / Render
# -----------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
