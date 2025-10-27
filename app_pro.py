import os
from loguru import logger
from flask import Flask, render_template, url_for, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import NotFound, InternalServerError

from extensions import (
    db, migrate, mail, cache, scheduler, login_manager, csrf, init_extensions, redis_client
)

app = Flask(__name__, static_folder="static", template_folder="templates")

config_name = os.getenv("FLASK_CONFIG", "config.config_production")
app.config.from_object(config_name)
logger.info(f"🚀 PittState-Connect launching in {config_name}")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

init_extensions(app)

def safe_url_for(endpoint_name, **values):
    try:
        return url_for(endpoint_name, **values)
    except Exception:
        return "#"

app.jinja_env.globals["safe_url_for"] = safe_url_for

def register_blueprint_safely(import_path, bp_name, url_prefix=None):
    try:
        module = __import__(import_path, fromlist=[bp_name])
        bp = getattr(module, bp_name)
        app.register_blueprint(bp, url_prefix=url_prefix)
        logger.info(f"✅ Loaded blueprint: {bp_name} ({url_prefix or '/'})")
    except Exception as e:
        from flask import Blueprint
        stub = Blueprint(bp_name, __name__)

        @stub.route("/")
        def stub_index():
            return jsonify({"stub": True, "blueprint": bp_name, "reason": str(e)}), 501

        app.register_blueprint(stub, url_prefix=url_prefix)
        logger.warning(f"⚠️ Using STUB blueprint for {bp_name} ({url_prefix}): {e}")

register_blueprint_safely("blueprints.core.routes", "core_bp", "/")
register_blueprint_safely("blueprints.auth.routes", "auth_bp", "/auth")
register_blueprint_safely("blueprints.careers.routes", "careers_bp", "/careers")
register_blueprint_safely("blueprints.departments.routes", "departments_bp", "/departments")
register_blueprint_safely("blueprints.scholarships.routes", "scholarships_bp", "/scholarships")
register_blueprint_safely("blueprints.faculty.routes", "faculty_bp", "/faculty")
register_blueprint_safely("blueprints.analytics.routes", "analytics_bp", "/analytics")
register_blueprint_safely("blueprints.alumni.routes", "alumni_bp", "/alumni")
register_blueprint_safely("blueprints.donor.routes", "donor_bp", "/donor")
register_blueprint_safely("blueprints.notifications.routes", "notifications_bp", "/notifications")

try:
    scheduler.add_job(
        id="nightly_analytics_refresh",
        func="blueprints.analytics.tasks:refresh_insight_cache",
        trigger="cron",
        hour=3,
    )
    scheduler.add_job(
        id="faculty_reindex",
        func="blueprints.faculty.tasks:rebuild_search_index",
        trigger="cron",
        hour=4,
    )
except Exception as e:
    logger.warning(f"⚠️ Skipped scheduler job registration: {e}")

@app.errorhandler(NotFound)
def error_404(e):
    logger.error("404 Error: Page not found")
    return render_template("errors/404.html"), 404

@app.errorhandler(InternalServerError)
def error_500(e):
    logger.exception("500 Error: Internal Server Error")
    return render_template("errors/500.html"), 500

@app.route("/maintenance")
def maintenance_page():
    return render_template("errors/maintenance.html"), 503

@app.route("/coming-soon")
def coming_soon_page():
    return render_template("errors/coming_soon.html"), 200

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "redis": bool(redis_client)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False)
