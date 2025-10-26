import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, url_for, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound

# --- Optional integrations present in your repo layout ---
# If any of these are missing in your environment, they’ll fail gracefully.
try:
    from extensions import db, migrate, login_manager, mail, socketio, cache  # your shared extensions
except Exception:  # fallback so this file won’t crash if one is missing at import time
    db = migrate = login_manager = mail = socketio = cache = None

# Blueprints already known to exist from your logs
from blueprints.core.routes import core_bp
from blueprints.analytics.routes import analytics_bp
from blueprints.departments.routes import departments_bp

# NEW: Careers blueprint (added below)
from blueprints.careers.routes import careers_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # -----------------------------
    # Configuration
    # -----------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ENV"] = os.getenv("FLASK_ENV", "production")
    app.config["PREFERRED_URL_SCHEME"] = os.getenv("URL_SCHEME", "https")

    # Caching (optional)
    if cache:
        cache_cfg = {
            "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
            "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "120")),
        }
        app.config.update(cache_cfg)
        try:
            cache.init_app(app)
        except Exception:
            pass

    # CORS
    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    # Extensions
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)
    if login_manager:
        login_manager.init_app(app)
        login_manager.login_view = "core_bp.login"
    if mail:
        mail.init_app(app)
    if socketio:
        # NOTE: gunicorn + eventlet/gevent as appropriate in your Procfile
        socketio.init_app(app, cors_allowed_origins="*")

    # -----------------------------
    # Logging (production-safe)
    # -----------------------------
    if not app.debug and not app.testing:
        log_dir = os.getenv("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"), maxBytes=5_000_000, backupCount=3
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s")
        )
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # -----------------------------
    # Jinja helpers (prevents 500s if endpoints are missing)
    # -----------------------------
    def has_endpoint(endpoint_name: str) -> bool:
        return endpoint_name in app.view_functions

    def safe_url_for(endpoint_name: str, **values) -> str:
        if has_endpoint(endpoint_name):
            return url_for(endpoint_name, **values)
        return "#"

    app.jinja_env.globals["has_endpoint"] = has_endpoint
    app.jinja_env.globals["safe_url_for"] = safe_url_for
    app.jinja_env.globals["now"] = lambda: datetime.utcnow()

    # -----------------------------
    # Blueprints
    # -----------------------------
    app.register_blueprint(core_bp)
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(departments_bp, url_prefix="/departments")
    app.register_blueprint(careers_bp, url_prefix="/careers")

    # -----------------------------
    # Health / readiness probes
    # -----------------------------
    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", time=datetime.utcnow().isoformat() + "Z"), 200

    @app.get("/readiness")
    def readiness():
        # Optionally verify DB connectivity
        try:
            if db:
                db.session.execute(db.text("SELECT 1"))
            return jsonify(ready=True), 200
        except Exception as e:
            app.logger.exception("Readiness check failed")
            return jsonify(ready=False, error=str(e)), 503

    # -----------------------------
    # Error handlers
    # -----------------------------
    @app.errorhandler(HTTPException)
    def http_error(e: HTTPException):
        code = e.code or 500
        # Avoid recursion: templates/errors/*.html extend base.html,
        # but base.html is safe now due to safe_url_for + has_endpoint checks.
        template = "errors/404.html" if isinstance(e, NotFound) else "errors/500.html"
        try:
            return render_template(template, error=e), code
        except Exception:  # final fallback
            return f"{code} error", code

    @app.errorhandler(Exception)
    def server_error(e):
        app.logger.exception("[uncaught] %s", e)
        try:
            return render_template("errors/500.html", error=e), 500
        except Exception:
            return "500 internal server error", 500

    # Example structured request logging
    @app.after_request
    def after_request(resp):
        try:
            app.logger.info(
                "method=%s path=%s status=%s length=%s ua=%s",
                request.method,
                request.path,
                resp.status_code,
                resp.calculate_content_length() or 0,
                request.headers.get("User-Agent", "-"),
            )
        except Exception:
            pass
        return resp

    return app


# For gunicorn: app_pro:app
app = create_app()

if __name__ == "__main__":
    # Local dev runner
    if socketio:
        socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
    else:
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
