"""
🦍 Gorilla-Link / PittState-Connect
-----------------------------------
Main Flask application entrypoint (Render production build)

Handles:
• App initialization (Flask + SQLAlchemy + Redis)
• Blueprint auto-registration
• PSU branding + environment configuration
• Optional route redirect for homepage
"""

import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# -------------------------------------------------
# 🔧 1. Environment setup
# -------------------------------------------------
load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# -------------------------------------------------
# 🧩 2. Flask Application Factory
# -------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")

# Email settings (Office 365 / PSU)
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

# Redis (optional cache or background queue)
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")

# -------------------------------------------------
# ⚙️ 3. Extension initialization
# -------------------------------------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
cache = Cache(app, config={"CACHE_TYPE": "simple"})
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# -------------------------------------------------
# 🧱 4. Blueprint Auto-Registration
# -------------------------------------------------
def register_blueprints():
    """Auto-detect and register all blueprints in /blueprints."""
    import importlib
    import pkgutil

    blueprints_pkg = "blueprints"
    package = importlib.import_module(blueprints_pkg)

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg:
            try:
                module = importlib.import_module(f"{blueprints_pkg}.{module_name}.routes")
                if hasattr(module, "bp"):
                    app.register_blueprint(module.bp)
                    print(f"✅ Loaded blueprint package: {module_name}")
            except Exception as e:
                print(f"⚠️ Failed to load blueprint '{module_name}': {e}")

register_blueprints()

# -------------------------------------------------
# 🏠 5. Root Redirect Route (Fixes 404 on Render root)
# -------------------------------------------------
@app.route("/")
def index_redirect():
    """Redirect '/' to PSU-branded Gorilla-Link home."""
    try:
        return redirect(url_for("core.home"))
    except Exception:
        # Fallback route if 'core.home' isn't found
        return redirect(url_for("feed.dashboard"))

# -------------------------------------------------
# 🧪 6. Health Check (for Render)
# -------------------------------------------------
@app.route("/health")
def health_check():
    return {"status": "ok", "message": "Gorilla-Link backend running successfully"}, 200

# -------------------------------------------------
# 🧠 7. Optional startup message
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Starting Gorilla-Link Flask server...")
    app.run(host="0.0.0.0", port=port)
