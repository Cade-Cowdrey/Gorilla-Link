import os
from flask import Flask, url_for, Markup
from config.config_production import ConfigProduction
from extensions import init_extensions, scheduler
from blueprints import register_blueprints
from utils.analytics_util import track_page_view
from loguru import logger

# ----------------------------
# APP FACTORY
# ----------------------------

app = Flask(__name__)
app.config.from_object(ConfigProduction)

# Initialize all extensions
init_extensions(app)
register_blueprints(app)

# Add safe_url_for globally for Jinja templates
def safe_url_for(endpoint, **values):
    """Return a safe URL or '#' if route doesn't exist."""
    try:
        return url_for(endpoint, **values)
    except Exception:
        return "#"

app.jinja_env.globals["safe_url_for"] = safe_url_for

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
# ROOT ROUTE
# ----------------------------

@app.route("/")
def index():
    return "🦍 PittState-Connect Production is Live!"

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
