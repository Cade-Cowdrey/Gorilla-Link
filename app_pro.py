import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, current_app
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from redis import Redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# --------------------------------------------------------------------
# Load environment & setup globals
# --------------------------------------------------------------------
load_dotenv()
db = SQLAlchemy()
mail = Mail()
scheduler = BackgroundScheduler()
redis_client = None

# --------------------------------------------------------------------
# Configuration Classes
# --------------------------------------------------------------------
class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "psu_secret")
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

# --------------------------------------------------------------------
# Helper: Select environment config
# --------------------------------------------------------------------
def select_config():
    env = os.getenv("FLASK_ENV", "production").lower()
    config = DevConfig if env == "development" else ProdConfig
    print(f"[config] Selecting configuration for environment: {env}")
    return config

# --------------------------------------------------------------------
# Background Job: Analytics Collector (with context safety)
# --------------------------------------------------------------------
def collect_usage_metrics():
    """Hourly analytics aggregation (runs under app context)."""
    try:
        with current_app.app_context():
            app = current_app
            app.logger.info("[Scheduler] Running analytics job...")
            now = datetime.utcnow().isoformat()

            # Example cache update
            redis_client.hset("psu:last_metrics", "last_run", now)
            app.logger.info(f"[Scheduler] Metrics collected successfully @ {now}")
    except Exception as e:
        print(f"Scheduler error: {e}")

# --------------------------------------------------------------------
# Create Flask App
# --------------------------------------------------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(select_config())

    # ----------------------------------------------------------------
    # Logging Setup
    # ----------------------------------------------------------------
    log_level = logging.INFO
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    app.logger.info("Logging configured successfully.")

    # ----------------------------------------------------------------
    # Extensions Initialization
    # ----------------------------------------------------------------
    CORS(app)
    db.init_app(app)
    mail.init_app(app)

    # Rate limiter with Redis backend (if available)
    limiter = Limiter(
        get_remote_address,
        app=app,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
        default_limits=["100 per minute"]
    )

    # Redis Client (for caching and metrics)
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        app.logger.info("✅ Redis connected successfully.")
    except Exception as e:
        redis_client = None
        app.logger.warning(f"⚠️ Redis unavailable: {e}")

    # APScheduler
    scheduler.start()
    scheduler.add_job(collect_usage_metrics, "interval", hours=1, id="usage_metrics")
    app.logger.info("✅ Background scheduler started.")

    # ----------------------------------------------------------------
    # Flask-Login setup
    # ----------------------------------------------------------------
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"

    # ----------------------------------------------------------------
    # Optional: Sentry integration (only if DSN set)
    # ----------------------------------------------------------------
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

    # ----------------------------------------------------------------
    # PSU Branding Globals
    # ----------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": app.config["PSU_BRAND"],
            "GOOGLE_ANALYTICS_ID": os.getenv("GOOGLE_ANALYTICS_ID", ""),
            "now": datetime.utcnow
        }

    # ----------------------------------------------------------------
    # Blueprint Registration (with safe context)
    # ----------------------------------------------------------------
    with app.app_context():
        from blueprints.core.routes import core_bp
        from blueprints.auth.routes import auth_bp
        from blueprints.careers.routes import careers_bp
        from blueprints.departments.routes import departments_bp
        from blueprints.scholarships.routes import scholarships_bp
        from blueprints.mentors.routes import mentors_bp
        from blueprints.alumni.routes import alumni_bp
        from blueprints.donor.routes import donor_bp
        from blueprints.emails.routes import emails_bp
        from blueprints.notifications.routes import notifications_bp

        # Analytics blueprint wrapped safely
        try:
            from blueprints.analytics.routes import analytics_bp
        except Exception as e:
            from flask import Blueprint
            analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")
            app.logger.warning(f"Using STUB blueprint for analytics_bp (/analytics). Reason: {e}")

        # Register all blueprints
        for bp in [
            core_bp, auth_bp, careers_bp, departments_bp,
            scholarships_bp, mentors_bp, alumni_bp,
            analytics_bp, donor_bp, emails_bp, notifications_bp
        ]:
            try:
                app.register_blueprint(bp)
                app.logger.info(f"✅ Registered blueprint: {bp.name}")
            except Exception as e:
                app.logger.warning(f"⚠️ Failed to register blueprint {bp.name}: {e}")

    # ----------------------------------------------------------------
    # OpenAI Key Verification
    # ----------------------------------------------------------------
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            app.logger.info("✅ OpenAI API key loaded successfully.")
        except Exception as e:
            app.logger.warning(f"⚠️ OpenAI key error: {e}")

    # ----------------------------------------------------------------
    # Error Handlers
    # ----------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server Error: %s", e)
        return render_template("errors/500.html"), 500

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200

    return app
