import os
from flask import Flask, url_for, render_template
from markupsafe import Markup
from config.config_production import ConfigProduction
from extensions import init_extensions, scheduler
from blueprints import register_blueprints
from loguru import logger

# ----------------------------
# APP FACTORY
# Force rebuild: 2025-11-05
# ----------------------------

app = Flask(__name__)
app.config.from_object(ConfigProduction)

# Initialize extensions first
init_extensions(app)

# ----------------------------
# GLOBAL JINJA HELPERS
# ----------------------------

def safe_url_for(endpoint, **values):
    """Return a safe URL or '#' if route doesn't exist."""
    try:
        return url_for(endpoint, **values)
    except Exception:
        return "#"

def has_endpoint(endpoint):
    """Check if a Flask endpoint exists (used in templates)."""
    return endpoint in app.view_functions

# Register both helpers globally before templates load
app.jinja_env.globals["safe_url_for"] = safe_url_for
app.jinja_env.globals["has_endpoint"] = has_endpoint

# ----------------------------
# BLUEPRINTS & ROUTES
# ----------------------------

register_blueprints(app)

# Register API v1 Blueprint
from blueprints.api.v1 import api_v1
app.register_blueprint(api_v1, url_prefix="/api/v1")

# Register GPA Calculator Blueprint
from blueprints.tools.gpa_calculator import gpa_bp
app.register_blueprint(gpa_bp)

# Register Dining Blueprint
from blueprints.dining.routes import dining_bp
app.register_blueprint(dining_bp)

# Register NEW Student Features Blueprints (8 new features!)
from blueprints.textbook_exchange.routes import textbook_bp
from blueprints.housing_reviews.routes import housing_bp
from blueprints.student_discounts.routes import discounts_bp
from blueprints.grade_explorer.routes import grade_explorer_bp
from blueprints.professor_reviews.routes import professor_bp
from blueprints.wait_times.routes import wait_times_bp
from blueprints.student_events.routes import events_bp
from blueprints.course_library.routes import course_library_bp

app.register_blueprint(textbook_bp)
app.register_blueprint(housing_bp)
app.register_blueprint(discounts_bp)
app.register_blueprint(grade_explorer_bp)
app.register_blueprint(professor_bp)
app.register_blueprint(wait_times_bp)
app.register_blueprint(events_bp)
app.register_blueprint(course_library_bp)

# Register Enhanced Admin Dashboard
from blueprints.admin_dashboard.routes import admin_dashboard_bp
app.register_blueprint(admin_dashboard_bp)

# Note: resume_bp is now auto-registered by register_blueprints()
# No need to manually register it here to avoid duplicate registration

@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# ERROR HANDLERS
# ----------------------------

@app.errorhandler(404)
def not_found(e):
    return Markup("<h3>404 - Page Not Found</h3>"), 404

@app.errorhandler(500)
def server_error(e):
    logger.exception("Server error: {}", e)
    return Markup("<h3>500 - Internal Server Error</h3>"), 500

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
