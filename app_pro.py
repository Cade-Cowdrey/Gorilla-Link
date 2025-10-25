# app_pro.py
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta
from flask import Flask, render_template, request, g
from flask_cors import CORS
from loguru import logger

from extensions import db, login_manager, cache, limiter, mail, migrate, socketio

# --- Configs ---------------------------------------------------
class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = 300

    RATELIMIT_DEFAULT = "200/hour"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    SECURITY_CSP = (
        "default-src 'self'; img-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.openai.com; "
        "object-src 'none'; frame-ancestors 'self';"
    )

    # Analytics flags
    ANALYTICS_DEMO_MODE = os.getenv("ANALYTICS_DEMO_MODE", "true")
    ANALYTICS_REQUIRE_LOGIN = os.getenv("ANALYTICS_REQUIRE_LOGIN", "false")
    FEATURE_SMARTMATCH_AI = os.getenv("FEATURE_SMARTMATCH_AI", "true")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class ProdConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db")
    PREFERRED_URL_SCHEME = "https"

class DevConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    DEBUG = True

# --- Factory ---------------------------------------------------
def create_app() -> Flask:
    env = os.getenv("FLASK_ENV", "production").lower()
    cfg = ProdConfig if env == "production" else DevConfig
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(cfg)

    # Logging
    _configure_logging(app)

    # CORS
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Extensions init
    db.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"

    # Request Loader (token or header-based auth)
    @login_manager.request_loader
    def load_user_from_request(req):
        # 1) Authorization: Bearer <token>
        auth = req.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            from models import User
            return User.query.filter_by(api_token=token).first()
        # 2) X-Auth-Token header
        token = req.headers.get("X-Auth-Token")
        if token:
            from models import User
            return User.query.filter_by(api_token=token).first()
        return None

    # Blueprints
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

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(scholarships_bp)
    app.register_blueprint(mentors_bp)
    app.register_blueprint(alumni_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(notifications_bp)

    logger.info("✅ Registered blueprints.")

    # Global security headers
    @app.after_request
    def _secure(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "interest-cohort=()")
        resp.headers.setdefault("Content-Security-Policy", app.config["SECURITY_CSP"])
        return resp

    # Errors
    @app.errorhandler(401)
    def unauthorized(_e): return render_template("errors/401.html"), 401

    @app.errorhandler(404)
    def not_found(_e): return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def ratelimited(_e): return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(_e): return render_template("errors/500.html"), 500

    return app

def _configure_logging(app: Flask):
    app.logger.setLevel(logging.INFO)
    logger.remove()
    logger.add(lambda msg: app.logger.info(msg.rstrip("\n")), level="INFO")

    log_dir = os.getenv("LOG_DIR")
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=5_000_000, backupCount=3)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.logger.info("Logging configured successfully.")

app = create_app()
