"""
PittState-Connect | Production Application Entrypoint
Fully PSU-branded, production-ready Flask app for Render.
Includes caching, Redis, CSRF, limiter, scheduler, analytics, and error handlers.
"""

import os
from loguru import logger
from flask import Flask, render_template, redirect, url_for
from extensions import (
    db, migrate, login_manager, mail, cache,
    limiter, scheduler, redis_client, csrf, init_extensions
)

# ======================================================
# 🧭 Config Selection
# ======================================================
from config.config_production import config_production

# ======================================================
# 🦍 App Factory
# ======================================================
def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Load configuration
    app.config.from_object(config_production)

    # Initialize all Flask extensions
    init_extensions(app)

    # ==================================================
    # 🧱 Blueprints Auto-Registration
    # ==================================================
    from blueprints import register_blueprints
    register_blueprints(app)

    # ==================================================
    # ⚙️ Error Handlers
    # ==================================================
    @app.errorhandler(401)
    def error_401(_):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def error_403(_):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def error_404(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def error_429(_):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def error_500(_):
        return render_template("errors/500.html"), 500

    # ==================================================
    # 🧰 Maintenance Mode
    # ==================================================
    @app.before_request
    def check_maintenance_mode():
        if app.config.get("MAINTENANCE_MODE"):
            return render_template("errors/maintenance.html"), 503

    # ==================================================
    # 🚧 Coming Soon Placeholder
    # ==================================================
    @app.route("/coming-soon")
    def coming_soon():
        return render_template("errors/coming_soon.html")

    return app


# ======================================================
# 🧠 App Instance
# ======================================================
app = create_app()

# ======================================================
# 🧾 Logging Setup
# ======================================================
log_level = app.config.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=log_level,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>"
)

# Use safe fallback for environment name
env_name = getattr(app, "env", "production").title()

logger.info(f"🚀 PittState-Connect launching in {env_name} mode.")
logger.info(f"📦 Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
logger.info(f"🔗 Redis: {app.config.get('REDIS_URL')}")
logger.info(f"📬 Mail: {app.config.get('MAIL_SERVER')}")

# ======================================================
# ✅ WSGI Entry Point
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
