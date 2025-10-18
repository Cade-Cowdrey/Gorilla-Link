"""
🦍 Gorilla-Link / PittState-Connect
Production Flask Application Entry Point
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
import os

# ---------------------------------------------
# 🔧 Environment Setup
# ---------------------------------------------
load_dotenv()

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# ---------------------------------------------
# ⚙️ Configurations
# ---------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///local.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-2025")

# Mail
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

# Redis / Cache
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ---------------------------------------------
# 🧩 Extensions
# ---------------------------------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
cache = Cache(app)
login_manager = LoginManager(app)
CORS(app)

# Limiter (basic rate limiting)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    default_limits=["100 per minute"]
)

# ---------------------------------------------
# 🔌 Auto-Register Blueprints
# ---------------------------------------------
def register_blueprints():
    import importlib
    import pkgutil

    package_name = "blueprints"
    package = importlib.import_module(package_name)

    for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
        if not ispkg:
            module = importlib.import_module(f"{package_name}.{modname}")
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
                print(f"✅ Registered blueprint: {modname}")

register_blueprints()

# ---------------------------------------------
# 👤 Login Manager Configuration
# ---------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# ---------------------------------------------
# 🧠 Context Processors
# ---------------------------------------------
@app.context_processor
def inject_branding():
    return {
        "psu_brand": "PittState-Connect",
        "psu_colors": {"primary": "#CC0000", "accent": "#FFD700"},
        "university": "Pittsburg State University",
    }

# ---------------------------------------------
# ❤️ Health Check Endpoint (for Render)
# ---------------------------------------------
@app.route("/health")
def health_check():
    try:
        db.session.execute("SELECT 1;")
        mail_status = "configured" if app.config.get("MAIL_USERNAME") else "not configured"
        return jsonify({
            "status": "ok",
            "database": "connected",
            "mail": mail_status,
            "blueprints": list(app.blueprints.keys()),
            "branding": "PSU theme active",
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ---------------------------------------------
# 🚀 Application Entry Point
# ---------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
