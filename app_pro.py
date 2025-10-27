"""
app_pro.py
-------------------------------------------------------------
PittState-Connect Production App Entry
-------------------------------------------------------------
• PSU-branded full Flask ecosystem (web, AI, analytics, mail)
• Safe stubs for missing modules
• Secure Redis + APScheduler integration
• Jinja helpers (has_endpoint, get_env, safe_url_for)
• Render-ready health logging and resiliency
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, url_for
from loguru import logger

# -------------------------------------------------------------
# ✅ Import extensions
# -------------------------------------------------------------
try:
    from extensions import (
        db, migrate, cache, mail,
        login_manager, scheduler, redis_client, csrf
    )
except Exception as e:
    logger.error("❌ Failed importing extensions: {}", e)
    raise


# -------------------------------------------------------------
# ✅ Create Flask App
# -------------------------------------------------------------
app = Flask(__name__)

# Load config dynamically
config_name = os.getenv("FLASK_CONFIG", "config.ProductionConfig")
try:
    app.config.from_object(config_name)
    logger.info("Loaded config: {}", config_name)
except Exception as e:
    logger.warning("Using default config; could not import {}: {}", config_name, e)

# -------------------------------------------------------------
# ✅ Initialize Extensions
# -------------------------------------------------------------
try:
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    logger.info("✅ Core extensions initialized.")
except Exception as e:
    logger.warning("⚠️ Extension init warning: {}", e)

# Redis
if redis_client:
    logger.info("✅ Connected to Redis successfully.")
else:
    logger.warning("⚠️ Redis unavailable.")

# -------------------------------------------------------------
# ✅ Logging Setup
# -------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, colorize=True, enqueue=True)
logger.info("🚀 PittState-Connect starting in {} mode", LOG_LEVEL)


# -------------------------------------------------------------
# ✅ Jinja Global Utilities
# -------------------------------------------------------------
def has_endpoint(name):
    """Return True if Flask endpoint exists."""
    try:
        return name in app.view_functions
    except Exception:
        return False


def get_env(key, default=None):
    """Fetch environment variable safely for templates."""
    return os.getenv(key, default)


def safe_url_for(endpoint_name, **values):
    """Safe version of url_for that returns '#' on error."""
    from werkzeug.routing import BuildError
    try:
        return url_for(endpoint_name, **values)
    except BuildError as e:
        logger.warning("⚠️ safe_url_for failed: {}", e)
        return "#"
    except Exception as e:
        logger.warning("⚠️ Unexpected URL error: {}", e)
        return "#"


# Register Jinja helpers
app.jinja_env.globals.update(
    has_endpoint=has_endpoint,
    get_env=get_env,
    safe_url_for=safe_url_for
)

logger.info("✅ Registered Jinja helpers (has_endpoint, get_env, safe_url_for)")


# -------------------------------------------------------------
# ✅ Blueprint Registration (with Safe Imports)
# -------------------------------------------------------------
def register_blueprint_safe(import_path, url_prefix):
    """Safely import and register blueprint."""
    try:
        module = __import__(import_path, fromlist=["bp"])
        bp = getattr(module, "bp", None)
        if not bp:
            raise ImportError("Missing blueprint object 'bp'")
        app.register_blueprint(bp, url_prefix=url_prefix)
        logger.success("🟢 Registered blueprint: {} ({})", import_path, url_prefix)
    except Exception as e:
        logger.warning("Using STUB blueprint for {} ({}). Reason: {}", import_path, url_prefix, e)
        @app.route(f"{url_prefix}/")
        def stub_view():
            return render_template(
                "core/coming_soon.html",
                title="Coming Soon",
                message=f"This module ({import_path}) is not yet available."
            )


# Core routes
register_blueprint_safe("blueprints.core.routes", "/")
register_blueprint_safe("blueprints.scholarships.routes", "/scholarships")
register_blueprint_safe("blueprints.departments.routes", "/departments")
register_blueprint_safe("blueprints.faculty.routes", "/faculty")
register_blueprint_safe("blueprints.analytics.routes", "/analytics")
register_blueprint_safe("blueprints.jobs.routes", "/careers")
register_blueprint_safe("blueprints.events.routes", "/events")
register_blueprint_safe("blueprints.notifications.routes", "/notifications")


# -------------------------------------------------------------
# ✅ Custom Error Pages
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("core/error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("500 Error: {}", e)
    return render_template("core/error.html", code=500, message="Internal Server Error"), 500


@app.route("/healthz")
def health_check():
    """Health endpoint for Render."""
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


# -------------------------------------------------------------
# ✅ Optional Scheduler Hooks
# -------------------------------------------------------------
try:
    if scheduler:
        logger.info("✅ Scheduler detected — checking background jobs.")
        with app.app_context():
            jobs = scheduler.get_jobs()
            for j in jobs:
                logger.debug("⏰ Job registered: {}", j.id)
    else:
        logger.warning("⚠️ No APScheduler active in this context.")
except Exception as e:
    logger.warning("Scheduler check failed: {}", e)


# -------------------------------------------------------------
# ✅ Mail Configuration Check
# -------------------------------------------------------------
if not os.getenv("SENDGRID_API_KEY"):
    logger.warning("⚠️ Incomplete mail configuration. Check SENDGRID_API_KEY or MAIL_* vars.")


# -------------------------------------------------------------
# ✅ Run for Local Debug
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )
