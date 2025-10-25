# app_pro.py
from __future__ import annotations

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

from flask import Flask, jsonify, render_template, g
from flask_cors import CORS
from flask_caching import Cache
from flask_session import Session
from flask_talisman import Talisman
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix

from utils.mail import init_mail, mail  # email utils
from utils.analytics import AnalyticsService  # app-scoped analytics service
from jobs.scheduler import init_scheduler  # APScheduler init (app-context safe)

try:
    import sentry_sdk  # optional
    from sentry_sdk.integrations.flask import FlaskIntegration
except Exception:  # pragma: no cover
    sentry_sdk = None

# ----------------------------
# Globals (extensions)
# ----------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()

# ----------------------------
# Configuration
# ----------------------------
class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "redis" if os.environ.get("REDIS_URL") else "filesystem"
    SESSION_REDIS = os.environ.get("REDIS_URL")  # jobs.scheduler converts this if str
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)

    CACHE_TYPE = "SimpleCache" if not os.environ.get("REDIS_URL") else "RedisCache"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 60

    # Security/CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    CORS_SUPPORTS_CREDENTIALS = True

    # Talisman / CSP
    TALISMAN_FORCE_HTTPS = True
    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": ["'self'"],
        "img-src": ["'self'", "data:", "https:"],
        "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "script-src": ["'self'", "https://www.googletagmanager.com", "https://cdn.jsdelivr.net"],
        "font-src": ["'self'", "https://cdn.jsdelivr.net", "data:"],
        "connect-src": ["'self'", "https://www.google-analytics.com"],
    }

    # Branding + Analytics
    PSU_BRAND = {
        "crimson": "#990000",
        "gold": "#FFC72C",
        "smoke": "#f8f9fa",
        "gradient": "linear-gradient(90deg, #990000 0%, #b0191e 50%, #FFC72C 100%)",
        "favicon": "/static/img/psu-favicon.png",
        "tagline": "Once a Gorilla, Always a Gorilla.",
    }
    GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "G-XXXXXXX")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

class ProdConfig(BaseConfig):
    ENV = "production"

class DevConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    TALISMAN_FORCE_HTTPS = False

def select_config() -> type[BaseConfig]:
    env = os.environ.get("FLASK_ENV") or os.environ.get("ENV") or "production"
    print(f"[config] Selecting configuration for environment: {env}")
    return ProdConfig if env.lower().startswith("prod") else DevConfig

# ----------------------------
# App Factory
# ----------------------------
def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    app.config.from_object(select_config())
    print(f"[config] Loaded config: {app.config.__class__.__name__}")

    # Robust logging (file + stdout)
    _configure_logging(app)

    # Sentry (optional)
    _boot_sentry(app)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app, config={"CACHE_TYPE": app.config["CACHE_TYPE"], "CACHE_REDIS_URL": app.config.get("CACHE_REDIS_URL"), "CACHE_DEFAULT_TIMEOUT": app.config["CACHE_DEFAULT_TIMEOUT"]})
    Session(app)
    Compress(app)
    init_mail(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"

    # Security headers via Talisman
    Talisman(
        app,
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", True),
        content_security_policy=app.config.get("TALISMAN_CONTENT_SECURITY_POLICY"),
        session_cookie_secure=True,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
        permissions_policy={
            "geolocation": "()",
            "camera": "()",
            "microphone": "()",
            "fullscreen": "*",
        },
    )

    # CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
        expose_headers=["Content-Type", "X-Request-Id"],
        max_age=600,
    )

    # Analytics service bound to app
    app.analytics = AnalyticsService(app)

    # Blueprints
    _register_blueprints(app)

    # Context processors + error handlers
    _register_context(app)
    _register_errors(app)

    # Scheduler (runs inside app context safe)
    init_scheduler(app)

    return app

# ----------------------------
# Helpers
# ----------------------------
def _configure_logging(app: Flask) -> None:
    # Turn env LOG_LEVEL into valid level
    level = logging.getLevelName(app.config.get("LOG_LEVEL", "INFO"))
    if isinstance(level, str):
        level = logging.INFO

    logging.basicConfig(level=level)
    app.logger.setLevel(level)

    log_dir = os.environ.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=1_000_000, backupCount=5)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"))
    app.logger.addHandler(file_handler)
    app.logger.info("Logging configured successfully.")

def _boot_sentry(app: Flask) -> None:
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn or not sentry_sdk:
        print("[config] No Sentry DSN found — skipping error tracking.")
        return
    sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()], traces_sample_rate=float(os.environ.get("SENTRY_TRACES", "0.0")))
    print("[config] Sentry initialized.")

def _register_blueprints(app: Flask) -> None:
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
    from blueprints.api.routes import api_bp

    bps = [
        core_bp, auth_bp, careers_bp, departments_bp, scholarships_bp, mentors_bp,
        alumni_bp, analytics_bp, donor_bp, emails_bp, notifications_bp, api_bp,
    ]
    for bp in bps:
        app.register_blueprint(bp)
        app.logger.info(f"✅ Registered blueprint: {bp.name.split('.')[0]}")

def _register_context(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": app.config["PSU_BRAND"],
            "GOOGLE_ANALYTICS_ID": app.config.get("GOOGLE_ANALYTICS_ID", ""),
        }

def _register_errors(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled 500: %r", e)
        return render_template("errors/500.html"), 500

    @app.get("/healthz")
    def healthz():
        # lightweight health endpoint
        return jsonify({"ok": True}), 200


# ----------------------------
# App entry (for gunicorn)
# ----------------------------
app = create_app()

# Optional local dev run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
