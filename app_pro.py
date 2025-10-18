# ---------------------------------------------
#  PittState-Connect / Gorilla-Link
#  APP_PRO.PY — PSU Final (UI + API ready)
# ---------------------------------------------
import os
from datetime import datetime
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
from models import db, User
from utils.mail_util import init_mail

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Core config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

    # Cache (Redis)
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Extensions
    db.init_app(app)
    Migrate(app, db)
    Cache(app)
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    init_mail(app)

    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Jinja global for now()
    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow}

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("core/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("core/500.html"), 500

    # Auto-register blueprints (aligned to your repo)
    import importlib
    blueprints = [
        "auth", "admin", "core", "feed", "career", "analytics", "departments",
        "campus", "alumni", "connections", "mentorship", "portfolio", "stories",
        "opportunities", "map", "engagement", "profile", "badges", "events",
        "notifications", "students", "api", "marketing", "digests", "groups"
    ]
    for bp_name in blueprints:
        try:
            module = importlib.import_module(f"blueprints.{bp_name}.routes")
            blueprint = getattr(module, f"{bp_name}_bp", None)
            if blueprint:
                app.register_blueprint(blueprint)
                print(f"✅ Loaded blueprint package: {bp_name}")
            else:
                print(f"⚠️  Skipped blueprint {bp_name}: missing {bp_name}_bp in routes.py")
        except Exception as e:
            print(f"⚠️  Skipped blueprint {bp_name}: {e}")

    # Root route (+ optional maintenance)
    @app.route("/")
    def index():
        if os.getenv("MAINTENANCE_MODE", "off").lower() == "on":
            return render_template("core/maintenance.html"), 503
        return render_template("core/home.html")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
