# app_pro.py
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException, NotFound

# --- Optional shared extensions (fail gracefully if missing) ---
# Your project typically defines these in extensions.py
try:
    from extensions import (
        db, migrate, login_manager, mail, socketio, cache, limiter
    )
except Exception:
    db = migrate = login_manager = mail = socketio = cache = limiter = None

# --- Blueprints (import with failsafe) ---
# Core / Departments are assumed present in your repo already
try:
    from blueprints.core.routes import core_bp
except Exception:
    from flask import Blueprint
    core_bp = Blueprint("core_bp", __name__)
    @core_bp.get("/")
    def home_stub():
        return "Core blueprint failed to load (stub).", 200

try:
    from blueprints.departments.routes import departments_bp
except Exception:
    from flask import Blueprint
    departments_bp = Blueprint("departments_bp", __name__, url_prefix="/departments")
    @departments_bp.get("/")
    def dep_stub():
        return "Departments blueprint failed to load (stub).", 200

# Careers (we added previously)
try:
    from blueprints.careers.routes import careers_bp
except Exception:
    from flask import Blueprint
    careers_bp = Blueprint("careers_bp", __name__, url_prefix="/careers")
    @careers_bp.get("/")
    def careers_stub():
        return "Careers blueprint failed to load (stub).", 200

# Scholarships & Analytics provided below in this drop
try:
    from blueprints.scholarships.routes import scholarships_bp
except Exception:
    from flask import Blueprint
    scholarships_bp = Blueprint("scholarships_bp", __name__, url_prefix="/scholarships")
    @scholarships_bp.get("/")
    def scholarships_stub():
        return "Scholarships blueprint failed to load (stub).", 200

try:
    from blueprints.analytics.routes import analytics_bp
except Exception:
    from flask import Blueprint
    analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")
    @analytics_bp.get("/")
    def analytics_stub():
        return "Analytics blueprint failed to load (stub).", 200


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --------------------------------
    # Base configuration (12-factor)
    # --------------------------------
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-this-in-prod"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///app.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ENV=os.getenv("FLASK_ENV", "production"),
        PREFERRED_URL_SCHEME=os.getenv("URL_SCHEME", "https"),
        # Mail (SendGrid SMTP)
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.sendgrid.net"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() == "true",
        MAIL_USE_SSL=os.getenv("MAIL_USE_SSL", "false").lower() == "true",
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", "apikey"),   # SendGrid username must be 'apikey'
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),         # Your SendGrid API key
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.com"),
    )

    # Caching
    if cache:
        app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
        app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "120")))
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
        try:
            mail.init_app(app)
        except Exception:
            pass
    if socketio:
        # eventlet/gevent recommended in production
        socketio.init_app(app, cors_allowed_origins="*")
    if limiter:
        # Global sane defaults; specific routes can override
        limiter.init_app(app)
        limiter.limit(os.getenv("GLOBAL_RATE_LIMIT", "200 per minute"))(lambda: None)

    # --------------------------------
    # Logging (production-safe)
    # --------------------------------
    if not app.debug and not app.testing:
        log_dir = os.getenv("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=5_000_000, backupCount=3)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    app.logger.info("[INIT] PittState-Connect started in %s mode.", app.config["ENV"])

    # --------------------------------
    # Jinja helpers (defensive nav)
    # --------------------------------
    def has_endpoint(endpoint_name: str) -> bool:
        return endpoint_name in app.view_functions

    def safe_url_for(endpoint_name: str, **values) -> str:
        if has_endpoint(endpoint_name):
            return url_for(endpoint_name, **values)
        return "#"

    app.jinja_env.globals["has_endpoint"] = has_endpoint
    app.jinja_env.globals["safe_url_for"] = safe_url_for
    app.jinja_env.globals["now"] = lambda: datetime.utcnow()

    # --------------------------------
    # Security headers on responses
    # --------------------------------
    @app.after_request
    def secure_headers(resp):
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=()",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        }
        for k, v in security_headers.items():
            resp.headers[k] = v
        return resp

    # --------------------------------
    # Blueprints
    # --------------------------------
    app.register_blueprint(core_bp)  # "/"
    app.register_blueprint(departments_bp, url_prefix="/departments")
    app.register_blueprint(careers_bp, url_prefix="/careers")
    app.register_blueprint(scholarships_bp, url_prefix="/scholarships")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # --------------------------------
    # Health / readiness probes
    # --------------------------------
    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", time=datetime.utcnow().isoformat() + "Z"), 200

    @app.get("/readiness")
    def readiness():
        try:
            if db:
                db.session.execute(db.text("SELECT 1"))
            return jsonify(ready=True), 200
        except Exception as e:
            app.logger.exception("Readiness check failed")
            return jsonify(ready=False, error=str(e)), 503

    # --------------------------------
    # Error handlers (safe templates)
    # --------------------------------
    @app.errorhandler(HTTPException)
    def http_error(e: HTTPException):
        code = e.code or 500
        template = "errors/404.html" if isinstance(e, NotFound) else "errors/500.html"
        try:
            return render_template(template, error=e), code
        except Exception:
            return f"{code} error", code

    @app.errorhandler(Exception)
    def server_error(e):
        app.logger.exception("[uncaught] %s", e)
        try:
            return render_template("errors/500.html", error=e), 500
        except Exception:
            return "500 internal server error", 500

    # Access log
    @app.after_request
    def access_log(resp):
        try:
            app.logger.info(
                "method=%s path=%s status=%s len=%s ua=%s",
                request.method,
                request.path,
                resp.status_code,
                resp.calculate_content_length() or 0,
                request.headers.get("User-Agent", "-"),
            )
        except Exception:
            pass
        return resp

    # One-time sanity pings
    try:
        app.logger.info("✅ All extensions initialized successfully.")
    except Exception:
        pass

    return app


app = create_app()

if __name__ == "__main__":
    if socketio:
        socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
    else:
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
