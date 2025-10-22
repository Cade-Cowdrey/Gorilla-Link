# ============================================================
# FILE: app_pro.py
# PittState-Connect — Production-ready Flask app (Render-safe)
# ============================================================

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from flask import Flask, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Optional performance (graceful if missing)
try:
    from flask_compress import Compress  # type: ignore
except Exception:
    Compress = None  # not required


# ------------------------------------------------------------
# 1) Extensions (MODULE-SCOPE)  ✅ importable from other files
# ------------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()


# ------------------------------------------------------------
# 2) Logging config (Render-friendly, single stdout handler)
# ------------------------------------------------------------
def _configure_logging(app: Flask) -> None:
    level_name = (app.config.get("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Remove default flask logger handlers to prevent duplicates
    for h in list(app.logger.handlers):
        app.logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(level)

    # Quiet down noisy libs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ------------------------------------------------------------
# 3) Jinja helpers (globals, filters, cache-busting for static)
# ------------------------------------------------------------
def _register_jinja(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "APP_NAME": app.config.get("APP_NAME", "PittState-Connect"),
            "UNIVERSITY_NAME": app.config.get(
                "UNIVERSITY_NAME", "Pittsburg State University"
            ),
        }

    def url_for_cachebust(endpoint: str, **values):
        # Add ?v=mtime to static assets for safe cache-busting
        if endpoint == "static" and "filename" in values:
            try:
                static_folder = Path(app.static_folder or "static")
                fp = static_folder / values["filename"]
                if fp.exists():
                    values["v"] = int(fp.stat().st_mtime)
            except Exception:
                pass
        return url_for(endpoint, **values)

    @app.template_filter("dt")
    def format_dt(val, fmt="%b %d, %Y %I:%M %p"):
        if not val:
            return ""
        if isinstance(val, (int, float)):
            val = datetime.utcfromtimestamp(val)
        return val.strftime(fmt)

    app.jinja_env.globals["url_for_cachebust"] = url_for_cachebust


# ------------------------------------------------------------
# 4) Security headers (with CSP tuned for current templates)
# ------------------------------------------------------------
def _register_security(app: Flask) -> None:
    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["X-XSS-Protection"] = "1; mode=block"

        # If you later externalize inline CSS/JS from base.html, remove 'unsafe-inline'.
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        resp.headers["Content-Security-Policy"] = csp
        resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return resp


# ------------------------------------------------------------
# 5) Blueprint registration helper
# ------------------------------------------------------------
def _register_blueprints(app: Flask) -> List[str]:
    """
    Import and register all app blueprints.
    Returns the list of registered blueprint names (for logging/testing).
    """
    from blueprints import (  # type: ignore
        core_bp,
        auth_bp,
        careers_bp,
        departments_bp,
        scholarships_bp,
        mentors_bp,          # present in your logs
        alumni_bp,
        analytics_bp,
        donor_bp,
        emails_bp,
        notifications_bp,    # present in your logs
    )

    bps = [
        core_bp,
        auth_bp,
        careers_bp,
        departments_bp,
        scholarships_bp,
        mentors_bp,
        alumni_bp,
        analytics_bp,
        donor_bp,
        emails_bp,
        notifications_bp,
    ]

    names = []
    for bp in bps:
        app.register_blueprint(bp)
        app.logger.info("✅ Registered blueprint: %s (%s)", bp.name, bp.url_prefix or "root")
        names.append(bp.name)
    app.logger.info("✅ All blueprints registered successfully.")
    return names


# ------------------------------------------------------------
# 6) App factory
# ------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Behind Render’s proxy so URL scheme/remote addr are correct
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore

    # Dynamic config (dev vs prod)
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        app.config.from_object("config.config_dev.DevConfig")
    else:
        app.config.from_object("config.Config")

    # Logging first
    _configure_logging(app)
    app.logger.info("Booting %s (env=%s)", app.config.get("APP_NAME", "PittState-Connect"), env)

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    if Compress:
        Compress(app)
        app.logger.info("Compression enabled (flask-compress).")
    else:
        app.logger.info("flask-compress not installed; skipping compression.")

    # Login manager config
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # Jinja + security
    _register_jinja(app)
    _register_security(app)

    # Blueprints
    try:
        registered = _register_blueprints(app)
        app.logger.debug("Blueprints list: %s", registered)
    except Exception as e:
        app.logger.exception("❌ Blueprint registration failed: %s", e)

    # Models + DB bootstrap (safe no-op if migrations already applied)
    with app.app_context():
        try:
            import models  # noqa: F401
            db.create_all()
            app.logger.info("📦 Database tables ensured/created.")
        except Exception as e:
            app.logger.exception("❌ Database bootstrap failed: %s", e)

    # Health/diagnostic routes (template-free, never break boot)
    @app.route("/healthz")
    def healthz():
        return jsonify(
            status="ok",
            app=app.config.get("APP_NAME", "PittState-Connect"),
            env=env,
            time=datetime.utcnow().isoformat() + "Z",
        )

    @app.route("/_debug/config")
    def debug_config():
        if not app.debug:
            return jsonify(error="Not available"), 404
        return jsonify(
            ENV=env,
            DEBUG=app.config.get("DEBUG"),
            DB_URI=app.config.get("SQLALCHEMY_DATABASE_URI"),
            MAIL_SERVER=app.config.get("MAIL_SERVER"),
            APP_NAME=app.config.get("APP_NAME"),
            UNIVERSITY_NAME=app.config.get("UNIVERSITY_NAME"),
        )

    # Minimal error handlers that don't rely on templates
    @app.errorhandler(404)
    def not_found(e):
        return "<h1>404 — Not Found</h1><p>Route not found.</p>", 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("500 Internal Server Error: %s", e)
        return "<h1>500 — Internal Server Error</h1><p>Something went wrong.</p>", 500

    # Startup banner
    app.logger.info(
        "\n🦍  %s started\nEnvironment: %s\nDatabase: %s\nDebug: %s\n-------------------------------------------",
        app.config.get("APP_NAME", "PittState-Connect"),
        env.upper(),
        app.config.get("SQLALCHEMY_DATABASE_URI"),
        app.config.get("DEBUG"),
    )

    return app


# ------------------------------------------------------------
# 7) Entrypoint (for local dev) — Render uses gunicorn start
# ------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
