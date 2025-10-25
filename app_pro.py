import os
from datetime import datetime, timedelta
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.ProdConfig")

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    CORS(app)

    # Blueprints
    from blueprints.core.routes import core_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.analytics.routes import analytics_bp
    from blueprints.careers.routes import careers_bp
    from blueprints.departments.routes import departments_bp
    from blueprints.scholarships.routes import scholarships_bp
    from blueprints.alumni.routes import alumni_bp
    from blueprints.donor.routes import donor_bp
    from blueprints.notifications.routes import notifications_bp
    from blueprints.api.routes import api_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(scholarships_bp)
    app.register_blueprint(alumni_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp)

    logger.info("✅ All blueprints registered successfully.")

    # --- Scheduler setup ---
    scheduler = BackgroundScheduler()
    scheduler.start()

    # Weekly Digest
    from utils.mail_util import send_weekly_analytics_digest
    def weekly_job():
        with app.app_context():
            send_weekly_analytics_digest("admin@pittstate.edu")
    scheduler.add_job(weekly_job, "cron", day_of_week="sun", hour=8, minute=0)

    # Monthly PDF Report
    from utils.mail_util import send_monthly_report_pdf
    def monthly_job():
        with app.app_context():
            now = datetime.utcnow()
            prev = (now.replace(day=1) - timedelta(days=1))
            send_monthly_report_pdf(["admin@pittstate.edu"], prev.month, prev.year)
    scheduler.add_job(monthly_job, "cron", day=1, hour=8, minute=0)

    logger.info("🕒 Scheduler initialized: weekly + monthly jobs active.")

    # --- Error Handlers ---
    @app.errorhandler(403)
    def forbidden(e): return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e): return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e): return render_template("errors/500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
