import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, session, abort, request, g
from extensions import db, migrate, login_manager, mail, cache, limiter, scheduler, redis_client
from config import config_production

# --------------------------------------------------------
# ✅ Create Flask App (Production)
# --------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(config_production)

# --------------------------------------------------------
# ✅ Initialize Extensions
# --------------------------------------------------------
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
mail.init_app(app)
cache.init_app(app)
limiter.init_app(app)
scheduler.init_app(app)
redis_client.init_app(app)

# --------------------------------------------------------
# ✅ Logging Setup
# --------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🚀 PittState-Connect launching in production mode")

# --------------------------------------------------------
# ✅ Maintenance Mode Middleware
# --------------------------------------------------------
@app.before_request
def check_maintenance_mode():
    """Redirect all non-admin traffic to maintenance page when active."""
    maintenance = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"
    g.maintenance_mode = maintenance  # pass to templates for banner display

    allowed_routes = ["/admin/toggle-maintenance", "/static/", "/favicon.ico"]

    if maintenance:
        # allow admin toggle access using ADMIN_TOKEN
        token = request.args.get("token")
        if any(request.path.startswith(p) for p in allowed_routes):
            return
        if token == os.getenv("ADMIN_TOKEN"):
            return  # allow admin bypass via token query
        return render_template("errors/maintenance.html"), 503

# --------------------------------------------------------
# ✅ Context Processor for Maintenance Banner
# --------------------------------------------------------
@app.context_processor
def inject_maintenance_banner():
    """Adds maintenance banner variable to all templates."""
    return {"maintenance_mode": g.get("maintenance_mode", False)}

# --------------------------------------------------------
# ✅ Secure Admin Toggle Route
# --------------------------------------------------------
@app.route("/admin/toggle-maintenance")
def toggle_maintenance():
    """Admin-only route to toggle maintenance mode."""
    admin_token = os.getenv("ADMIN_TOKEN")
    provided_token = request.args.get("token")

    if not provided_token or provided_token != admin_token:
        abort(403)

    current_value = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"
    new_value = "False" if current_value else "True"
    os.environ["MAINTENANCE_MODE"] = new_value

    status = "disabled" if current_value else "enabled"
    logger.warning(f"⚙️ Maintenance mode {status.upper()} by admin at {datetime.now()}")
    return f"<h3>Maintenance mode {status}.<br>Reload the site to apply changes.</h3>"

# --------------------------------------------------------
# ✅ Register Blueprints
# --------------------------------------------------------
try:
    from blueprints.core.routes import core_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.admin.routes import admin_bp
    from blueprints.analytics.routes import analytics_bp
    from blueprints.scholarships.routes import scholarships_bp
    from blueprints.alumni.routes import alumni_bp
    from blueprints.career.routes import career_bp
    from blueprints.notifications.routes import notifications_bp
    from blueprints.messages.routes import messages_bp
    from blueprints.events.routes import events_bp
    from blueprints.departments.routes import departments_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(scholarships_bp)
    app.register_blueprint(alumni_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(departments_bp)
    logger.info("✅ All blueprints registered successfully")
except Exception as e:
    logger.error(f"❌ Blueprint registration failed: {e}")

# --------------------------------------------------------
# ✅ PSU-Branded Error Handlers
# --------------------------------------------------------
@app.errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500

# --------------------------------------------------------
# ✅ Default Route
# --------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("core_bp.home"))

# --------------------------------------------------------
# ✅ Scheduler Start
# --------------------------------------------------------
if not scheduler.running:
    scheduler.start()

# --------------------------------------------------------
# ✅ Gunicorn Entrypoint
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
