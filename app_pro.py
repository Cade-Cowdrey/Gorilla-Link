# app_pro.py
# PittState-Connect — Production-ready WSGI App (gunicorn target: app_pro:app)

from __future__ import annotations
import os, uuid, logging
from datetime import datetime
from typing import Optional

from flask import Flask, request, g, render_template, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

# Werkzeug 3.x compatibility — BuildError moved from exceptions → routing
try:
    from werkzeug.routing import BuildError
except ImportError:
    from werkzeug.exceptions import BuildError

# --------------------------------------------------------------------
# 🔌 Extensions (expected to exist in extensions.py)
# --------------------------------------------------------------------
from extensions import (
    db,
    migrate,
    cache,
    mail,
    scheduler,
    login_manager,
    CORS,
    redis_client,  # Optional
)


# --------------------------------------------------------------------
# ⚙️ Configuration Loader
# --------------------------------------------------------------------
def _load_config(app: Flask):
    cfg_env = os.getenv("CONFIG_CLASS")
    if cfg_env:
        app.config.from_object(cfg_env)
        return
    env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production").lower()
    try:
        if env.startswith("prod"):
            from config.settings import ProductionConfig as C
        elif env.startswith("dev"):
            from config.settings import DevelopmentConfig as C
        elif env.startswith("test"):
            from config.settings import TestingConfig as C
        else:
            from config.settings import ProductionConfig as C
        app.config.from_object(C)
    except Exception:
        app.config.update(
            SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
            SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///psu_connect.db"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Lax",
            WTF_CSRF_ENABLED=True,
            JSON_SORT_KEYS=False,
            CORS_RESOURCES={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}},
            SCHEDULER_API_ENABLED=False,
            TIMEZONE=os.getenv("TZ", "UTC"),
        )


# --------------------------------------------------------------------
# 🧱 App Factory
# --------------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    _load_config(app)

    # Respect proxy headers (Render)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)  # type: ignore

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    CORS(app, resources=app.config.get("CORS_RESOURCES", {r"/*": {"origins": "*"}}))
    scheduler.init_app(app)

    _setup_logging(app)
    _register_template_helpers(app)
    _register_request_response_hooks(app)
    _register_health_routes(app)
    _register_static_helpers(app)
    _register_blueprints(app)
    _register_jobs(app)
    _redis_smoke_test(app)

    app.logger.info("✅ PittState-Connect initialized successfully.")
    return app


# --------------------------------------------------------------------
# 🧾 Logging
# --------------------------------------------------------------------
def _setup_logging(app: Flask):
    logging.getLogger("werkzeug").setLevel(logging.INFO)

    @app.before_request
    def before():
        g.request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])

    @app.after_request
    def after(resp):
        try:
            app.logger.info(
                "%s %s %s %s %s",
                request.method,
                request.path,
                resp.status_code,
                resp.content_length or 0,
                request.user_agent.string,
            )
        except Exception:
            pass
        return resp


# --------------------------------------------------------------------
# 🧩 Template Helpers
# --------------------------------------------------------------------
def _register_template_helpers(app: Flask):
    from flask import url_for

    @app.template_global("safe_url_for")
    def safe_url_for(endpoint: str, **vals):
        try:
            return url_for(endpoint, **vals)
        except BuildError:
            app.logger.warning("safe_url_for: invalid endpoint %s", endpoint)
            return "#"

    @app.template_filter("datefmt")
    def datefmt(value: Optional[datetime], fmt="%Y-%m-%d"):
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except Exception:
                return value
        return value.strftime(fmt)


# --------------------------------------------------------------------
# 🛡️ Security Headers & Error Pages
# --------------------------------------------------------------------
def _register_request_response_hooks(app: Flask):
    @app.after_request
    def secure(resp):
        csp = (
            "default-src 'self'; img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' https: data:; connect-src 'self' https:;"
        )
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "no-referrer-when-downgrade")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
        resp.headers.setdefault("Content-Security-Policy", csp)
        if request.headers.get("X-Forwarded-Proto") == "https":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return resp

    @app.errorhandler(404)
    def not_found(_):
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            return jsonify(error="Not Found"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("500 Error: %s", e)
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return jsonify(error="Server Error"), 500


# --------------------------------------------------------------------
# 💓 Health & Readiness
# --------------------------------------------------------------------
def _register_health_routes(app: Flask):
    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True, ts=datetime.utcnow().isoformat())

    @app.get("/readiness")
    def ready():
        db_ok = cache_ok = True
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db_ok = False
        try:
            cache.set("readiness:ping", "1", timeout=5)
        except Exception:
            cache_ok = False
        return jsonify(ok=db_ok and cache_ok, db=db_ok, cache=cache_ok)


# --------------------------------------------------------------------
# 🗂️ Static passthrough (for debugging)
# --------------------------------------------------------------------
def _register_static_helpers(app: Flask):
    @app.get("/static/<path:filename>")
    def static_passthrough(filename):
        return send_from_directory(app.static_folder, filename)


# --------------------------------------------------------------------
# 🧱 Blueprint Registration (with Stub Fallback)
# --------------------------------------------------------------------
def _register_blueprints(app: Flask):
    from flask import Blueprint

    def register(name, import_path, url_prefix=None):
        try:
            mod = __import__(import_path, fromlist=["*"])
            bp = getattr(mod, name)
            app.register_blueprint(bp, url_prefix=url_prefix)
            app.logger.info("Loaded blueprint: %s (%s)", name, url_prefix or "/")
        except Exception as err:
            reason = str(err).split("\n", 1)[0]
            stub = Blueprint(name, __name__, url_prefix=url_prefix or "/")

            @stub.get("/")
            def _stub():
                return f"{name} temporarily unavailable — {reason}", 200

            app.register_blueprint(stub)
            app.logger.warning("Stubbed %s (%s): %s", name, url_prefix, reason)

    # Primary blueprints
    register("core_bp", "blueprints.core.routes")
    register("auth_bp", "blueprints.auth.routes", "/auth")
    register("careers_bp", "blueprints.careers.routes", "/careers")
    register("departments_bp", "blueprints.departments.routes", "/departments")
    register("faculty_bp", "blueprints.faculty.routes", "/faculty")
    register("scholarships_bp", "blueprints.scholarships.routes", "/scholarships")
    register("mentors_bp", "blueprints.mentors.routes", "/mentors")
    register("alumni_bp", "blueprints.alumni.routes", "/alumni")
    register("analytics_bp", "blueprints.analytics.routes", "/analytics")
    register("donor_bp", "blueprints.donor.routes", "/donor")
    register("emails_bp", "blueprints.emails.routes", "/emails")
    register("notifications_bp", "blueprints.notifications.routes", "/notifications")


# --------------------------------------------------------------------
# 🕒 Scheduler Jobs
# --------------------------------------------------------------------
def _register_jobs(app: Flask):
    scheduler.start(paused=True)
    jobs = [
        ("nightly_analytics_refresh", "blueprints.analytics.tasks:refresh_insight_cache", 2),
        ("faculty_reindex", "blueprints.faculty.tasks:rebuild_search_index", 3),
    ]
    added = 0
    for job_id, path, hour in jobs:
        try:
            scheduler.add_job(
                id=job_id,
                func=path,
                trigger="cron",
                hour=hour,
                replace_existing=True,
            )
            added += 1
        except Exception as e:
            app.logger.warning("Skipped job %s: %s", job_id, e)
    scheduler.resume()
    app.logger.info("🕒 Scheduler active — %s jobs loaded", added)


# --------------------------------------------------------------------
# 🔁 Redis Smoke Test
# --------------------------------------------------------------------
def _redis_smoke_test(app: Flask):
    try:
        if redis_client:
            redis_client.set("startup:ping", "ok", ex=30)
            app.logger.info("✅ Redis connection OK")
        else:
            app.logger.warning("⚠️ Redis client missing (extensions.redis_client=None)")
    except Exception as e:
        app.logger.warning("⚠️ Redis unavailable: %s", e)


# --------------------------------------------------------------------
# 🏁 App Export for Gunicorn
# --------------------------------------------------------------------
def _fallback_index():
    return "PittState-Connect is running.", 200


app = create_app()
if not any(r.rule == "/" for r in app.url_map.iter_rules()):
    app.add_url_rule("/", "index", _fallback_index)

if os.getenv("PRINT_ROUTES_ON_BOOT") == "1":
    with app.app_context():
        print("\n=== BLUEPRINTS ===")
        for n, bp in app.blueprints.items():
            print(f"{n:25s} -> {bp.url_prefix}")
        print("\n=== ROUTES ===")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            print(f"{rule.rule:40s} [{methods}] -> {rule.endpoint}")
        print()
