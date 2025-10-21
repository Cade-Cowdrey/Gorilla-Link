import os
from flask import Flask
from flask_migrate import Migrate
from extensions import db, mail, login_manager
from blueprints import register_all_blueprints
from models import User


# ------------------------------
# Flask Factory Setup
# ------------------------------

def create_app():
    app = Flask(__name__)

    # ------------------------------
    # Configuration
    # ------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gorillalink-devkey-23890")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///pittstate_connect.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # SendGrid / Mail
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("SENDGRID_USERNAME", "apikey")
    app.config["MAIL_PASSWORD"] = os.getenv("SENDGRID_API_KEY", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
        "MAIL_DEFAULT_SENDER", "no-reply@pittstate.edu"
    )

    # AWS / Cloud storage
    app.config["S3_BUCKET"] = os.getenv("S3_BUCKET")
    app.config["S3_REGION"] = os.getenv("S3_REGION")
    app.config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
    app.config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")

    # ------------------------------
    # Init extensions
    # ------------------------------
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # ------------------------------
    # Flask-Login configuration
    # ------------------------------
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        """Required by Flask-Login: loads a user from the database by ID."""
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # ------------------------------
    # Blueprint auto-registration
    # ------------------------------
    register_all_blueprints(app)

    # ------------------------------
    # Global context variables
    # ------------------------------
    @app.context_processor
    def inject_globals():
        return {"app_name": "PittState-Connect"}

    # ------------------------------
    # Health check route
    # ------------------------------
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


# ------------------------------
# WSGI entry point
# ------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
