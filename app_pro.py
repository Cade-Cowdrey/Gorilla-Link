# ============================================================
# FILE: app_pro.py
# Main Flask application factory for PittState-Connect (Render-ready)
# ============================================================

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Optional: gzip/deflate responses if library is available
try:
    from flask_compress import Compress  # type: ignore
except Exception:  # pragma: no cover
    Compress = None  # graceful fallback

# ------------------------------------------------------------
# Extensions (initialized without app context)
# ------------------------------------------------------------
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()


# ------------------------------------------------------------
# Helper: configure structured logging to stdout (Render-friendly)
# ------------------------------------------------------------
def _configure_logging(app: Flask) -> None:
    level_name = app.config.get("LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    # Clear default handlers to avoid duplicate logs in some WSGI hosts
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
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ------------------------------------------------------------
# Helper: Jinja globals & filters
# ------------------------------------------------------------
def _register_jinja_helpers(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "APP_NAME": app.config.get("APP_NAME", "PittState-Connect"),
            "UNIVERSITY_NAME": app.config.get(
                "UNIVERSITY_NAME", "Pittsburg State University"
            ),
        }

    # Cache-busting for static assets based on file mtime (safe fallback)
    def url_for_cachebust(endpoint, **values):
        if endpoint == "static" and "filename" in values:
            try:
                static_folder = Path(app.static_folder or "static")
                file_path = static_folder / values["filename"]
                if file_path.exists():
                    values["v"] = int(file_path.stat().st_mtime)
            except Exception:
                # If anything fails, we still return a working URL without v
                pass
        return url_for(endpoint, **values)

    app.jinja_env.globals["url_for_cachebust"] = url_for_cachebust

    # Simple datetime format filter
    @app.template_filter("dt")
    def format_dt(val, fmt="%b %d, %Y %I:%M %p"):
        if not val:
            return ""
        if isinstance(val, (int, float)):
            val = datetime.utcfromtimestamp(val)
        return val.strftime(fmt)


# ------------------------------------------------------------
# Helper: Security headers (including CSP tuned for this project)
# ------------------------------------------------------------
def _register_security(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        # MIME/XSS/Frame protections
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy:
        # Note: using 'unsafe-inline' for script/style because base.html includes inline JS/CSS and animate.css.
        # If you later externalize scripts/styles, you can tighten this policy.
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
        response.headers["Content-Security-Policy"] = csp

        # Strict-Transport-Security for HTTPS (Render uses HTTPS at edge)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        return response


# ------------------------------------------------------------
# Application Factory
# ------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Behind Render's proxy (sets correct scheme/remote addr)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore

    # Dynamic Config
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        app.config.from_object("config.config_dev.DevConfig")
    else:
        app.config.from_object("config.Config")

    # Configure logging early
    _configure_logging(app)
    app.logger.info("Starting PittState-Connect with env=%s", env)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    if Compress:
        Compress(app)
        app.logger.info("Compression enabled (flask-compress)")
    else:
        app.logger.info("Compression not installed; skipping.")

    # LoginManager config
    login_manager.login_view = "auth_bp.login"
    login_manager.login_message_category = "info"

    # Jinja helpers
    _register_jinja_helpers(app)

    # Security headers
    _register_security(app)

    # --------------------------------------------------------
    # Register Blueprints
    # --------------------------------------------------------
    try:
        # The blueprints package should expose these objects
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
            # Add more here as new modules are added
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
            app.register_blueprint(bp)
            app.logger.info("✅ Registered blueprint: %s (%s)", bp.name, bp.url_prefix or "root")

        app.logger.info("✅ All blueprints registered successfully.")

    except Exception as e:
        app.logger.exception("❌ Blueprint registration failed: %s", e)
        # Do not raise — keep app booting so /healthz is still reachable
        # but you should fix the import errors.

    # --------------------------------------------------------
    # Models import (avoid circulars) & DB bootstrap
    # --------------------------------------------------------
    with app.app_context():
        try:
            import models  # noqa: F401
            db.create_all()  # Safe: no-op if already migrated
            app.logger.info("📦 Database tables ensured/created.")
        except Exception as e:
            app.logger.exception("❌ Database init failed: %s", e)

    # --------------------------------------------------------
    # Health & diagnostics routes
    # --------------------------------------------------------
    @app.route("/healthz")
    def healthz():
        """Simple health probe for Render."""
        return jsonify(
            status="ok",
            app=app.config.get("APP_NAME", "PittState-Connect"),
            env=env,
            time=datetime.utcnow().isoformat() + "Z",
        )

    @app.route("/_debug/config")
    def debug_config():
        """Show a safe subset of config (DEBUG only)."""
        if not app.debug:
            return jsonify(error="Not available"), 404
        safe = {
            "ENV": env,
            "DEBUG": app.config.get("DEBUG"),
            "SQLALCHEMY_DATABASE_URI": app.config.get("SQLALCHEMY_DATABASE_URI"),
            "MAIL_SERVER": app.config.get("MAIL_SERVER"),
            "APP_NAME": app.config.get("APP_NAME"),
            "UNIVERSITY_NAME": app.config.get("UNIVERSITY_NAME"),
        }
        return jsonify(safe)

    # --------------------------------------------------------
    # Error handlers (safe, template-free fallbacks)
    # --------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        # Keep it minimal so it never fails if templates move
        return (
            "<h1>404 — Not Found</h1><p>The page you're looking for doesn't exist.</p>",
            404,
        )

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("500 Internal Server Error: %s", e)
        return (
            "<h1>500 — Internal Server Error</h1><p>Something went wrong on our end.</p>",
            500,
        )

    # --------------------------------------------------------
    # Startup banner
    # --------------------------------------------------------
    app.logger.info(
        "\n🦍  %s started!\nEnvironment: %s\nDatabase: %s\nDebug: %s\n----------------------------------------------------------",
        app.config.get("APP_NAME", "PittState-Connect"),
        env.upper(),
        app.config.get("SQLALCHEMY_DATABASE_URI"),
        app.config.get("DEBUG"),
    )

    return app


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
