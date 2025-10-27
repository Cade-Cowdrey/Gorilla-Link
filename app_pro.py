"""
app_pro.py
--------------------------------------------------
PittState-Connect | Production Application Entrypoint
Full Render deployment build with PSU branding,
secure extensions, blueprint auto-loader, and
nightly maintenance jobs.
--------------------------------------------------
"""

import os
from flask import Flask, render_template, jsonify
from loguru import logger
from config import get_config
from extensions import db, migrate, cache, mail, scheduler, login_manager, init_extensions
from utils.mail_util import send_nightly_summary


# ==================================================
# 🔧 Factory
# ==================================================
def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(get_config())
    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_scheduler_jobs(app)
    return app


# ==================================================
# 🧩 Blueprints Loader (with safe stubbing)
# ==================================================
def register_blueprints(app):
    from importlib import import_module

    blueprints = [
        ("blueprints.core.routes", "core_bp"),
        ("blueprints.auth.routes", "auth_bp"),
        ("blueprints.profile.routes", "profile_bp"),
        ("blueprints.departments.routes", "departments_bp"),
        ("blueprints.faculty.routes", "faculty_bp"),
        ("blueprints.scholarships.routes", "scholarships_bp"),
        ("blueprints.analytics.routes", "analytics_bp"),
    ]

    for module_path, bp_name in blueprints:
        try:
            mod = import_module(module_path)
            bp = getattr(mod, bp_name)
            app.register_blueprint(bp)
            logger.info(f"✅ Registered {bp_name} ({module_path})")
        except Exception as e:
            from flask import Blueprint
            stub = Blueprint(bp_name, __name__, url_prefix=f"/{bp_name.replace('_bp','')}")
            logger.warning(f"⚠️ Using STUB blueprint for {bp_name} ({module_path}). Reason: {e}")
            app.register_blueprint(stub)


# ==================================================
# 🚨 Error Handlers
# ==================================================
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"404 Error: {e}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"500 Error: {e}")
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def unhandled(e):
        logger.exception(f"Unhandled Exception: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


# ==================================================
# 🌙 Nightly Jobs
# ==================================================
def register_scheduler_jobs(app):
    try:
        scheduler.add_job(
            id="nightly_email_summary",
            func=send_nightly_summary,
            trigger="cron",
            hour=2,
            minute=0,
        )
        logger.info("🌙 Nightly email summary job registered.")
    except Exception as e:
        logger.warning(f"⚠️ Could not schedule nightly jobs: {e}")


# ==================================================
# 🧠 AI / Analytics Placeholder (Optional Phase 3+)
# ==================================================
@app_pro_error = None
try:
    from utils.analytics_util import preload_analytics_cache
    preload_analytics_cache()
except Exception as e:
    app_pro_error = e
    logger.warning(f"⚠️ Analytics preload skipped: {e}")


# ==================================================
# 🦍 App Instance
# ==================================================
app = create_app()

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "PittState-Connect"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info(f"🚀 Starting PittState-Connect on port {port}")
    app.run(host="0.0.0.0", port=port)
