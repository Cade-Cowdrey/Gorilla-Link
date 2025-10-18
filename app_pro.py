import os
from flask import Flask, render_template, redirect, url_for
from extensions import init_extensions, db
from datetime import datetime

# -------------------------------------------------
# 🧩 BLUEPRINT IMPORTS
# -------------------------------------------------
from blueprints.core.routes import core
from blueprints.feed.routes import feed
from blueprints.careers.routes import careers
from blueprints.alumni.routes import alumni
from blueprints.profile.routes import profile
from blueprints.badges.routes import badges
from blueprints.notifications.routes import notifications
from blueprints.events.routes import events
from blueprints.auth.routes import auth
from blueprints.analytics.routes import analytics
from blueprints.admin.routes import admin


# -------------------------------------------------
# ⚙️ APP FACTORY
# -------------------------------------------------
def create_app():
    """Creates and configures the Flask app for PittState-Connect (production)."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---------------------------------------------
    # 🔒 CONFIGURATION
    # ---------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///pittstate_connect.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail (PSU branded)
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "noreply@pittstateconnect.edu")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.edu")

    # CORS / JSON
    app.config["JSON_SORT_KEYS"] = False

    # Initialize extensions
    init_extensions(app)

    # ---------------------------------------------
    # 📦 BLUEPRINT REGISTRATION
    # ---------------------------------------------
    app.register_blueprint(core, url_prefix="/")
    app.register_blueprint(feed, url_prefix="/")
    app.register_blueprint(careers, url_prefix="/")
    app.register_blueprint(alumni, url_prefix="/")
    app.register_blueprint(profile, url_prefix="/")
    app.register_blueprint(badges, url_prefix="/")
    app.register_blueprint(notifications, url_prefix="/")
    app.register_blueprint(events, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(analytics, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/")

    # ---------------------------------------------
    # 🧭 ERROR HANDLERS (PSU-BRANDED)
    # ---------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # ---------------------------------------------
    # 🔗 DEFAULT ROUTE
    # ---------------------------------------------
    @app.route("/")
    def root_redirect():
        """Redirect base domain to home."""
        return redirect(url_for("core.home"))

    # ---------------------------------------------
    # ✅ HEALTH CHECK (Render)
    # ---------------------------------------------
    @app.route("/health")
    def health_check():
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    return app


# -------------------------------------------------
# 🚀 PRODUCTION ENTRYPOINT
# -------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
