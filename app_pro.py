# app_pro.py
# PittState-Connect — Production WSGI App (gunicorn target: app_pro:app)

from __future__ import annotations

import os
import logging
import uuid
from datetime import datetime
from typing import Optional

from flask import (
    Flask,
    request,
    g,
    render_template,
    jsonify,
    send_from_directory,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import BuildError

# --- Extensions (must exist in extensions.py) ---
# Expected exports: db, migrate, cache, mail, scheduler, login_manager, CORS, redis_client
from extensions import (
    db,
    migrate,
    cache,
    mail,
    scheduler,
    login_manager,
    CORS,  # from flask_cors import CORS inside extensions
    redis_client,  # Optional; may be None if not configured
)

# ---------- Configuration loader ----------
def _load_config(app: Flask) -> None:
    """
    Load config from config package. Supports:
    - CONFIG_CLASS env var (e.g., 'config.settings.ProductionConfig')
    - APP_ENV env var (production | development | testing)
    Fallback to a minimal in-file production config if import fails.
    """
    cfg_env = os.getenv("CONFIG_CLASS")
    if cfg_env:
        app.config.from_object(cfg_env)
        return

    app_env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production").lower()
    try:
        if app_env.startswith("prod"):
            from config.settings import ProductionConfig as CFG  # type: ignore
        elif app_env.startswith("dev"):
            from config.settings import DevelopmentConfig as CFG  # type: ignore
        elif app_env.startswith("test"):
            from config.settings import TestingConfig as CFG  # type: ignore
        else:
            from config.settings import ProductionConfig as CFG  # type: ignore
        app.config.from_object(CFG)
    except Exception:
        # Minimal sane defaults if config import not available
        app.config.update(
            SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
            SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///psu_connect.db"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            PREFERRED_URL_SCHEME=os.getenv("PREFERRED_URL_SCHEME", "https"),
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Lax",
            WTF_CSRF_ENABLED=True,
            JSON_SORT_KEYS=False,
            # CORS defaults (tighten to your domain if desired)
            CORS_RESOURCES={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}},
            # APScheduler
            SCHEDULER_API_ENABLED=False,
            TIMEZONE=os.getenv("TZ", "UTC"),
        )


# ---------- App factory ----------
def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    _load_config(app)

    # Respect reverse proxy headers on Render (X-Forwarded-*)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)  # type: ignore

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # CORS (tighten as needed in config)
    CORS(app, resources=app.config.get("CORS_RESOURCES", {r"/*": {"origins": "*"}}))

    # Scheduler (load later after app context)
    scheduler.init_app(app)

    # Logging: gunicorn already logs; add request-bound context + concise app log
    _setup_logging(app)

    # Global helpers (Jinja + appcontext)
    _register_template_helpers(app)

    # Security headers + response normalization
    _register_request_response_hooks(app)

    # Health/readiness
    _register_health_routes(app)

    # Static helpers (optional direct file access for debugging missing assets)
    _register_static_helpers(app)

    # Blueprints (with resilient stub fallback)
    _register_blueprints(app)

    # Background jobs (safe registration)
    _register_jobs(app)

    # Redis smoke test
    _redis_smoke_test(app)

    app.logger.info("[INIT] PittState-Connect started in production mode.")
    app.logger.info("✅ All extensions initialized successfully.")
    return app


# ---------- Logging ----------
def _setup_logging(app: Flask) -> None:
    # Reduce Flask/werkzeug noise; gunicorn handles access logs
    logging.getLogger("werkzeug").setLevel(logging.INFO)

    @app.before_request
    def add_request_context():
        # Attach a short request id for correlation
        g.request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])

    @app.after_request
    def access_log(resp):
        # concise structured log line
        try:
            app.logger.info(
                "method=%s path=%s status=%s len=%s ua=%s",
                request.method,
                request.path,
                resp.status_code,
                resp.content_length or 0,
                request.user_agent.string,
            )
        except Exception:
            pass
        return resp


# ---------- Jinja & URL helpers ----------
def _register_template_helpers(app: Flask) -> None:
    @app.template_global("safe_url_for")
    def safe_url_for(endpoint_name: str, **values) -> str:
        """
        Guards against BuildError during template generation.
        Returns '#' when the endpoint or params are invalid.
        """
        from flask import url_for

        try:
            return url_for(endpoint_name, **values)
        except BuildError:
            app.logger.warning(
                "[safe_url_for] Could not build url for endpoint '%s' with values %s",
                endpoint_name,
                list(values.keys()),
            )
            return "#"

    # Jinja filters (examples)
    @app.template_filter("datefmt")
    def datefmt(value: Optional[datetime], fmt: str = "%Y-%m-%d") -> str:
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except Exception:
                return value  # leave as-is
        return value.strftime(fmt)


# ---------- Security & headers ----------
def _register_request_response_hooks(app: Flask) -> None:
    @app.after_request
    def set_secure_headers(resp):
        # DO NOT touch request.headers (immutable) — only response headers.
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' https: data:; "
            "connect-src 'self' https:;"
        )
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("X-XSS-Protection", "0")  # modern browsers
        resp.headers.setdefault("Referrer-Policy", "no-referrer-when-downgrade")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
        resp.headers.setdefault("Content-Security-Policy", csp)

        # HSTS (enable only when behind HTTPS)
        if request.headers.get("X-Forwarded-Proto", "http") == "https":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return resp

    # Error handlers
    @app.errorhandler(404)
    def not_found(_e):
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            return jsonify(error="Not Found", code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("500 Error: %s", e)
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return jsonify(error="Internal Server Error", code=500), 500


# ---------- Health / readiness ----------
def _register_health_routes(app: Flask) -> None:
    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True, ts=datetime.utcnow().isoformat())

    @app.get("/readiness")
    def readiness():
        # basic DB ping
        db_ok = True
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db_ok = False
        cache_ok = True
        try:
            cache.set("readiness:ping", "1", timeout=5)
        except Exception:
            cache_ok = False
        return jsonify(ok=db_ok and cache_ok, db=db_ok, cache=cache_ok, ts=datetime.utcnow().isoformat())


# ---------- Static helpers (optional) ----------
def _register_static_helpers(app: Flask) -> None:
    # Quick route to help spot missing assets during deploys
    @app.get("/static/<path:filename>")
    def static_passthrough(filename: str):
        return send_from_directory(app.static_folder, filename)


# ---------- Blueprint registration with graceful stubs ----------
def _register_blueprints(app: Flask) -> None:
    from flask import Blueprint

    def register(name: str, import_path: str, url_prefix: Optional[str] = None):
        """
        Try to import the blueprint; on failure, register a stub so the site loads.
        """
        try:
            module = __import__(import_path, fromlist=["*"])
            bp = getattr(module, name)
            app.register_blueprint(bp, url_prefix=url_prefix)
            app.logger.info("Loaded blueprint: %s (%s)", name, url_prefix or "/")
        except Exception as err:
            # create stub blueprint
            stub_name = name
            stub_prefix = url_prefix or "/"
            reason = str(err).split("\n", 1)[0]
            app.logger.warning("Using STUB blueprint for %s (%s). Reason: %s", stub_name, stub_prefix, reason)

            stub = Blueprint(stub_name, __name__, url_prefix=stub_prefix)

            @stub.get("/")
            def _stub_index():
                return (
                    f"{stub_name} is temporarily unavailable. "
                    f"(stub mounted; reason: {reason})"
                ), 200

            app.register_blueprint(stub, url_prefix=stub_prefix)

    # Core
    register("core_bp", "blueprints.core.routes", url_prefix=None)

    # Optional sections (mounted even if fall back to stubs)
    register("auth_bp", "blueprints.auth.routes", url_prefix="/auth")
    register("careers_bp", "blueprints.careers.routes", url_prefix="/careers")
    register("departments_bp", "blueprints.departments.routes", url_prefix="/departments")
    register("scholarships_bp", "blueprints.scholarships.routes", url_prefix="/scholarships")
    register("mentors_bp", "blueprints.mentors.routes", url_prefix="/mentors")
    register("alumni_bp", "blueprints.alumni.routes", url_prefix="/alumni")
    register("analytics_bp", "blueprints.analytics.routes", url_prefix="/analytics")
    register("donor_bp", "blueprints.donor.routes", url_prefix="/donor")
    register("emails_bp", "blueprints.emails.routes", url_prefix="/emails")
    register("notifications_bp", "blueprints.notifications.routes", url_prefix="/notifications")
    register("faculty_bp", "blueprints.faculty.routes", url_prefix="/faculty")


# ---------- Scheduler / Jobs ----------
def _register_jobs(app: Flask) -> None:
    """
    Register APScheduler jobs. If a job's import path is unavailable, skip safely.
    """
    # Always start scheduler (even if no jobs could be added)
    scheduler.start(paused=True)
    added = 0
    try:
        # Prefer import-by-string so APScheduler can resolve lazily
        scheduler.add_job(
            id="nightly_analytics_refresh",
            func="blueprints.analytics.tasks:refresh_insight_cache",
            trigger="cron",
            hour=2,  # 2AM UTC nightly
            replace_existing=True,
        )
        added += 1
    except Exception as e:
        app.logger.warning("Skipping job nightly_analytics_refresh (reason: %s)", str(e).split("\n", 1)[0])

    try:
        # Example: faculty search index refresh (optional)
        scheduler.add_job(
            id="faculty_search_reindex",
            func="blueprints.faculty.tasks:rebuild_search_index",
            trigger="cron",
            hour=3,
            replace_existing=True,
        )
        added += 1
    except Exception as e:
        app.logger.warning("Skipping job faculty_search_reindex (reason: %s)", str(e).split("\n", 1)[0])

    scheduler.resume()
    app.logger.info("🕒 Scheduler initialized. Jobs added: %s", added)


# ---------- Redis smoke test ----------
def _redis_smoke_test(app: Flask) -> None:
    try:
        if redis_client:
            key = "startup:redis_probe"
            redis_client.set(key, "ok", ex=30)
            app.logger.info("✅ Connected to Redis successfully.")
            app.logger.info("Redis test write succeeded.")
        else:
            app.logger.warning("⚠️ Redis client not configured (extensions.redis_client is None).")
    except Exception as e:
        app.logger.warning("⚠️ Redis unavailable: %s", e)


# ---------- Basic landing route (kept in core blueprint ideally) ----------
# We still expose '/' here defensively in case core_bp stubbed out.
def _fallback_index():
    return "PittState-Connect is running.", 200


# Create the global app for gunicorn
app = create_app()

# If core_bp failed and nothing mounted '/', ensure we still have an index.
if not any(r.rule == "/" for r in app.url_map.iter_rules()):
    app.add_url_rule("/", "index", _fallback_index)

# ---- Debug helper: list routes (disabled by default) ----
if os.getenv("PRINT_ROUTES_ON_BOOT") == "1":
    with app.app_context():
        print("\n=== ✅ REGISTERED BLUEPRINTS ===")
        for name, bp in app.blueprints.items():
            print(f"{name:25s} -> {bp.url_prefix}")
        print("\n=== ✅ REGISTERED ROUTES ===")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            print(f"{rule.rule:40s}  [{methods}]  ->  {rule.endpoint}")
        print()
