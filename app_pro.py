# app_pro.py
from __future__ import annotations
import os
import logging
from logging import StreamHandler
from datetime import datetime

from flask import Flask, render_template, g, request
from flask_cors import CORS
from flask_compress import Compress
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_login import LoginManager, current_user
from loguru import logger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# --- Globals (extensions) ---
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
sess = Session()

def select_config():
    env = os.getenv("FLASK_ENV") or os.getenv("ENV") or "production"
    print(f"[config] Selecting configuration for environment: {env}")
    class Base:
        SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pittstate.db").replace("postgres://", "postgresql://")
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SESSION_TYPE = "filesystem" if not os.getenv("REDIS_URL") else "redis"
        SESSION_REDIS = os.getenv("REDIS_URL")  # scheduler will connect separately
        CACHE_TYPE = "SimpleCache"
        CACHE_DEFAULT_TIMEOUT = 60
        CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "G-XXXXXXX")
        PSU_BRAND = {
            "favicon": "/static/img/psu-shield.png",
            "gradient": "linear-gradient(90deg, #990000, #b81212)",
            "tagline": "By Gorillas. For Gorillas.",
        }
        DIGEST_RECIPIENTS = [e.strip() for e in os.getenv("DIGEST_RECIPIENTS", "provost@pittstate.edu,it@pittstate.edu").split(",")]
    class Dev(Base):
        DEBUG = True
    class Prod(Base):
        DEBUG = False
    return Dev if env.startswith("dev") else Prod

def _to_level(name: str) -> int:
    return {
        "CRITICAL": logging.CRITICAL, "ERROR": logging.ERROR, "WARNING": logging.WARNING,
        "INFO": logging.INFO, "DEBUG": logging.DEBUG, "NOTSET": logging.NOTSET,
    }.get(str(name).upper(), logging.INFO)

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(select_config())

    # --- Logging (std + loguru bridge) ---
    level = _to_level(app.config.get("LOG_LEVEL", "INFO"))
    logging.basicConfig(level=level)
    handler = StreamHandler()
    handler.setLevel(level)
    app.logger.handlers = [handler]
    logger.remove()
    logger.add(lambda msg: app.logger.log(level, msg.rstrip()), level=level)
    logger.info("Logging configured successfully.")

    # --- Core extensions ---
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    Compress(app)
    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"

    # --- Rate limiting & sockets ---
    limiter = Limiter(key_func=get_remote_address, default_limits=["300 per minute"])
    limiter.init_app(app)
    app.extensions["limiter"] = limiter

    socketio = SocketIO(app, cors_allowed_origins="*")
    app.extensions["socketio"] = socketio

    # --- Context processors ---
    @app.context_processor
    def inject_globals():
        return {
            "PSU_BRAND": app.config["PSU_BRAND"],
            "GOOGLE_ANALYTICS_ID": app.config["GOOGLE_ANALYTICS_ID"],
            "now": datetime.utcnow,
        }

    # --- Simple user loader (placeholder) ---
    @login_manager.user_loader
    def load_user(user_id):
        # replace with real model lookup
        return None

    # --- Blueprints (existing + new) ---
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

    # New ones added in this bundle:
    from blueprints.announcements.routes import announcements_bp
    from blueprints.api.v2 import api_v2_bp

    for bp in [
        core_bp, auth_bp, analytics_bp, careers_bp, alumni_bp, departments_bp,
        emails_bp, donor_bp, scholarships_bp, mentors_bp, notifications_bp,
        announcements_bp, api_v2_bp,
    ]:
        app.register_blueprint(bp)
        app.logger.info(f"✅ Registered blueprint: {bp.name.split('.')[0]}")

    # --- Mail ---
    from utils.mail import init_mail
    init_mail(app)

    # --- Redis/session note ---
    if app.config.get("SESSION_TYPE") == "redis" and app.config.get("SESSION_REDIS"):
        try:
            import redis
            r = redis.from_url(app.config["SESSION_REDIS"])
            r.ping()
            app.logger.info("✅ Redis connected successfully.")
        except Exception as e:
            app.logger.warning(f"Redis not available: {e}")

    # --- Scheduler (runs in app context) ---
    from jobs.scheduler import init_scheduler
    init_scheduler(app)

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app

app = create_app()
