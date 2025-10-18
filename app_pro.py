# ============================================================
# 🦍 Gorilla-Link / PittState-Connect
# Production Flask App Entrypoint (Render-Ready)
# ============================================================

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv

# ============================================================
# 🔧 Environment setup
# ============================================================
load_dotenv()

# Explicitly tell Flask where to find PSU-branded static + templates
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# ============================================================
# ⚙️ Flask App Factory
# ============================================================
app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    template_folder=TEMPLATE_DIR
)

# ============================================================
# 🗄️ Configurations
# ============================================================
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")

# ============================================================
# 🧩 Extensions
# ============================================================
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
mail = Mail(app)
CORS(app)

# ============================================================
# 📦 Blueprint Auto-Loader
# ============================================================
def register_blueprints():
    from pathlib import Path
    import importlib

    blueprints_path = Path(BASE_DIR) / "blueprints"
    if not blueprints_path.exists():
        print("⚠️  No blueprints directory found.")
        return

    for module in blueprints_path.iterdir():
        if module.is_dir() and (module / "__init__.py").exists():
            try:
                bp = importlib.import_module(f"blueprints.{module.name}")
                if hasattr(bp, "bp"):
                    app.register_blueprint(bp.bp)
                    print(f"✅ Registered blueprint: {module.name}")
            except Exception as e:
                print(f"❌ Failed to register {module.name}: {e}")

register_blueprints()

# ============================================================
# 👤 Login & Routes
# ============================================================
login_manager.login_view = "auth.login"

@app.route("/")
def index():
    return "<h1>🦍 Gorilla-Link (PSU Branded Site)</h1><p>Flask app running successfully.</p>"

# ============================================================
# 🚀 App Export
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
