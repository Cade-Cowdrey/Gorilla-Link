"""
PittState-Connect Production Application Entrypoint
Full PSU-branded, secure, analytics-aware build
"""

import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    g,
)
from loguru import logger

# ======================================================
# 🔧 Extensions Import
# ======================================================
from extensions import (
    db,
    migrate,
    login_manager,
    mail,
    cache,
    scheduler,
    redis_client,
    csrf,
)

# ======================================================
# 🚀 Application Factory
# ======================================================
app = Flask(__name__, template_folder="templates", static_folder="static")

# ------------------------------------------------------
# Load Config
# ------------------------------------------------------
config_env = os.getenv("FLASK_ENV", "production").lower()
if config_env == "development":
    app.config.from_object("config.config_development")
else:
    app.config.from_object("config.config_production")

logger.info(f"🚀 PittState-Connect launching in {app.config['ENV'].title()} mode.")

# ======================================================
# 🔒 Core Security & Extensions Init
# ======================================================
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
mail.init_app(app)
cache.init_app(app)
csrf.init_app(app)

# Redis connectivity check
try:
    redis_client.ping()
    logger.info("✅ Connected to Redis successfully.")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")

# APScheduler setup
scheduler.init_app(app)
scheduler.start()
logger.info("🕓 Scheduler initialized and started successfully.")

# ======================================================
# 🧩 Register Blueprints
# ======================================================
def register_blueprint_safe(name, import_path, url_prefix):
    """Registers blueprints safely even if missing models."""
    try:
        module = __import__(import_path, fromlist=["bp"])
        app.register_blueprint(module.bp, url_prefix=url_prefix)
        logger.info(f"✅ Loaded blueprint: {name} ({url_prefix})")
    except Exception as e:
        from flask import Blueprint
        bp = Blueprint(name, __name__, url_prefix=url_prefix)

        @bp.route("/")
        def stub():
            return render_template(
                "errors/coming_soon.html",
                title=f"{name.title()} Coming Soon",
                code="🚧",
                heading=f"{name.title()} Coming Soon",
                message="This module is under construction or temporarily disabled.",
                icon="hammer",
            ), 200

        app.register_blueprint(bp, url_prefix=url_prefix)
        logger.warning(f"⚠️ Using stub for {name} ({url_prefix}): {e}")


register_blueprint_safe("core_bp", "blueprints.core.routes", "/")
register_blueprint_safe("auth_bp", "blueprints.auth.routes", "/auth")
register_blueprint_safe("scholarships_bp", "blueprints.scholarships.routes", "/scholarships")
register_blueprint_safe("departments_bp", "blueprints.departments.routes", "/departments")
register_blueprint_safe("faculty_bp", "blueprints.faculty.routes", "/faculty")
register_blueprint_safe("analytics_bp", "blueprints.analytics.routes", "/analytics")
register_blueprint_safe("careers_bp", "blueprints.careers.routes", "/careers")

# ======================================================
# 🧠 Context Processors
# ======================================================
@app.context_processor
def inject_globals():
    """Inject global PSU helpers and status banner context."""
    env = os.getenv("FLASK_ENV", "production")
    maintenance_mode = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"

    banner = None
    if maintenance_mode:
        banner = {"color": "bg-yellow-500", "text": "Maintenance Mode: limited access", "icon": "wrench"}
    elif env == "development":
        banner = {"color": "bg-blue-600", "text": "Development Environment", "icon": "code"}
    else:
        banner = {"color": "bg-green-600", "text": "All Systems Operational", "icon": "check-circle"}

    return {
        "now": datetime.utcnow,
        "env": env,
        "status_banner": banner,
    }

# ======================================================
# 🧱 Maintenance Mode Hook
# ======================================================
@app.before_request
def check_maintenance_mode():
    if os.getenv("MAINTENANCE_MODE", "False").lower() == "true":
        if not request.path.startswith("/admin"):
            return render_template("errors/maintenance.html"), 503

# ======================================================
# 🌐 Simple Health Check
# ======================================================
@app.route("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "db": "connected" if db.engine else "unavailable",
        "redis": "connected" if redis_client else "unavailable",
        "time": datetime.utcnow().isoformat()
    })

# ======================================================
# ⚠️ Error Handlers (PSU-Branded)
# ======================================================
@app.errorhandler(401)
def unauthorized_error(error):
    return render_template("errors/401.html"), 401

@app.errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(429)
def too_many_requests(error):
    return render_template("errors/429.html"), 429

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500

# ======================================================
# 🕓 Scheduled Jobs
# ======================================================
@scheduler.task("cron", id="nightly_analytics_refresh", hour=2)
def nightly_analytics_refresh():
    """Nightly cache refresh for analytics dashboards."""
    logger.info("🌙 Running nightly analytics refresh...")
    try:
        from blueprints.analytics.tasks import refresh_insight_cache
        refresh_insight_cache()
        logger.info("✅ Analytics cache refreshed successfully.")
    except Exception as e:
        logger.error(f"❌ Nightly analytics refresh failed: {e}")

@scheduler.task("interval", id="faculty_reindex", hours=12)
def faculty_reindex():
    """Rebuilds faculty search index every 12 hours."""
    try:
        from blueprints.faculty.tasks import rebuild_search_index
        rebuild_search_index()
        logger.info("🔍 Faculty index rebuilt successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Faculty reindex failed: {e}")

# ======================================================
# 🦍 PSU-Themed 404 Fallback (root test)
# ======================================================
@app.route("/test404")
def test_404():
    return render_template("errors/404.html"), 404

# ======================================================
# 🧩 App Runner
# ======================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
