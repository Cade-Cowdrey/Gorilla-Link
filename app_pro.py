import os
from flask import Flask, url_for
from markupsafe import Markup
from config.config_production import ConfigProduction
from extensions import init_extensions, scheduler
from blueprints import register_blueprints
from loguru import logger

# ----------------------------
# APP FACTORY
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

@app.route("/")
def index():
    return "🦍 PittState-Connect Production is Live!"

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
