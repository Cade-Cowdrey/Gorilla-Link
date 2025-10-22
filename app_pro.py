# ============================================================
# FILE: app_pro.py
# PittState-Connect — Advanced production Flask factory (Render-safe)
# ============================================================

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from flask import Flask, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Optional performance & metrics
try:
    from flask_compress import Compress  # gzip/deflate
except Exception:
    Compress = None

try:
    from prometheus_flask_exporter import PrometheusMetrics  # optional metrics
except Exception:
    PrometheusMetrics = None


# ------------------------------------------------------------
# 1️⃣ EXTENSIONS (singletons shared across blueprints)
# ------------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()


# ------------------------------------------------------------
# 2️⃣ LOGGING CONFIG (Render + Cloud optimized)
# ------------------------------------------------------------
def _configure_logging(app: Flask) -> None:
    """Configure simple JSON-like structured logging."""
    level_name = (app.config.get("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    for h in list(app.logger.handlers):
        app.logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(level)

    # Quiet noisy deps
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ------------------------------------------------------------
# 3️⃣ JINJA HELPERS (cache-busting, date formatting, globals)
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
# 4️⃣ SECURITY HEADERS (HSTS, CSP, anti-XSS)
# ------------------------------------------------------------
def _register_security(app: Flask) -> None:
    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers[
            "Strict-Transport-Security"
        ] = "max-age=63072000; includeSubDomains; preload"

        # CSP tuned for PSU assets
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self' https://api.openai.com; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        resp.headers["Content-Security-Policy"] = csp
        return resp


# ------------------------------------------------------------
# 5️⃣ BLUEPRINT REGISTRATION
# ------------------------------------------------------------
def _register_blueprints(app: Flask) -> List[str]:
    """Import and register all blueprints (auto-logs each)."""
    from blueprints import (
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
        app.logger.info("✅ Registered blueprint: %s (%s)", bp.name, bp.url_prefix or "")
        names.append(bp.name)
    return names


# ------------------------------------------------------------
# 6️⃣ APP FACTORY
# ------------------------------------------------------------
def create_app(config_name: Optional[str] = None) -> Flask:
    """Factory pattern — used by both Render (Gunicorn) & local dev."""
    app = Flask(__name__, instance_relative_config=False)

    # Fix proxy headers (Render load balancer)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore

    # Config selection
    env = config_name or os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        app.config.from_object("config.config_dev.DevConfig")
    else:
        app.config.from_object("config.Config")

    # Logging first
    _configure_logging(app)
    app.logger.info("🚀 Booting %s (env=%s)", app.config.get("APP_NAME"), env)

    # Extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    if Compress:
        Compress(app)
        app.logger.info("Compression: enabled")
    else:
        app.logger.info("Compression: not installed")

    # Optional: Prometheus metrics endpoint /metrics
    if PrometheusMetrics:
        PrometheusMetrics(app, group_by="endpoint")
        app.logger.info("Metrics: Prometheus exporter enabled")

    # Auth settings
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # Templates + Security
    _register_jinja(app)
    _register_security(app)

    # Blueprints
    try:
        _register_blueprints(app)
    except Exception as e:
        app.logger.exception("❌ Blueprint registration failed: %s", e)

    # DB bootstrapping
    with app.app_context():
        try:
            import models  # noqa: F401
            db.create_all()
            app.logger.info("📦 Database tables ensured.")
        except Exception as e:
            app.logger.exception("❌ DB bootstrap failed: %s", e)

    # Health check
    @app.route("/healthz")
    def healthz():
        return jsonify(
            status="ok",
            app=app.config.get("APP_NAME"),
            env=env,
            time=datetime.utcnow().isoformat() + "Z",
        )

    # Minimal error handlers
    @app.errorhandler(404)
    def not_found(e):
        return "<h1>404 — Not Found</h1><p>Route not found.</p>", 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("500 error: %s", e)
        return "<h1>500 — Internal Server Error</h1><p>Something went wrong.</p>", 500

    app.logger.info(
        "\n🦍  %s started\nEnvironment: %s\nDatabase: %s\nDebug: %s\n-------------------------------------------",
        app.config.get("APP_NAME", "PittState-Connect"),
        env.upper(),
        app.config.get("SQLALCHEMY_DATABASE_URI"),
        app.config.get("DEBUG"),
    )

    return app


# ------------------------------------------------------------
# 7️⃣ GLOBAL APP INSTANCE (for Gunicorn)
# ------------------------------------------------------------
# Gunicorn uses this when running `gunicorn app_pro:app`
app = create_app()


# ------------------------------------------------------------
# 8️⃣ LOCAL ENTRYPOINT
# ------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
