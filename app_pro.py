# app_pro.py
# ---------------------------------------------------------------------
# Production entrypoint for PittState-Connect
# - Central app factory pattern
# - Scheduler jobs for analytics, maintenance, and AI
# - PSU branding, advanced logging, security hardening
# ---------------------------------------------------------------------

import os
import logging
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

# ---------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------
from extensions import init_extensions, db, redis_client
from utils.mail_util import send_system_alert
from utils.analytics_util import flush_redis_to_db, get_dashboard_metrics
from utils.scheduler_util import monitor_scheduler_health

# ---------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------
def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # -----------------------------------------------------------------
    # Config
    # -----------------------------------------------------------------
    env = os.getenv("FLASK_ENV", "production")
    app.config.from_object(f"config.{env.capitalize()}Config")

    # -----------------------------------------------------------------
    # Logging setup
    # -----------------------------------------------------------------
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, "psu_app.log"))
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info(f"[INIT] PittState-Connect started in {env.upper()} mode.")

    # -----------------------------------------------------------------
    # Extension initialization
    # -----------------------------------------------------------------
    init_extensions(app)

    # Proxy fix (for Render + Nginx)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # -----------------------------------------------------------------
    # Rate Limiter
    # -----------------------------------------------------------------
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per hour"],
        storage_uri=os.getenv("REDIS_URL", "memory://"),
    )
    limiter.init_app(app)

    # -----------------------------------------------------------------
    # Blueprint registration
    # -----------------------------------------------------------------
    try:
        from blueprints.core.routes import core_bp
        from blueprints.auth.routes import auth_bp
        from blueprints.careers.routes import careers_bp
        from blueprints.departments.routes import departments_bp
        from blueprints.scholarships.routes import scholarships_bp
        from blueprints.mentors.routes import mentors_bp
        from blueprints.alumni.routes import alumni_bp
        from blueprints.analytics.routes import analytics_bp
        from blueprints.donor.routes import donor_bp
        from blueprints.emails.routes import emails_bp
        from blueprints.notifications.routes import notifications_bp

        app.register_blueprint(core_bp)
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(careers_bp, url_prefix="/careers")
        app.register_blueprint(departments_bp, url_prefix="/departments")
        app.register_blueprint(scholarships_bp, url_prefix="/scholarships")
        app.register_blueprint(mentors_bp, url_prefix="/mentors")
        app.register_blueprint(alumni_bp, url_prefix="/alumni")
        app.register_blueprint(analytics_bp, url_prefix="/analytics")
        app.register_blueprint(donor_bp, url_prefix="/donor")
        app.register_blueprint(emails_bp, url_prefix="/emails")
        app.register_blueprint(notifications_bp, url_prefix="/notifications")
        app.logger.info("✅ Blueprints registered successfully.")
    except Exception as e:
        app.logger.error(f"⚠️ Error loading blueprints: {e}")

    # -----------------------------------------------------------------
    # Scheduler configuration
    # -----------------------------------------------------------------
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")

    @scheduler.scheduled_job(IntervalTrigger(hours=1))
    def job_flush_redis():
        """Hourly Redis → DB analytics flush."""
        with app.app_context():
            flush_redis_to_db()
            app.logger.info("🧮 Analytics buffer flushed.")

    @scheduler.scheduled_job(IntervalTrigger(hours=12))
    def job_monitor_scheduler():
        """Monitor scheduler health every 12h."""
        with app.app_context():
            monitor_scheduler_health(app)
            app.logger.info("🩺 Scheduler health checked.")

    @scheduler.scheduled_job(IntervalTrigger(hours=24))
    def job_generate_metrics():
        """Daily summary snapshot for PSU Analytics Dashboard."""
        with app.app_context():
            metrics = get_dashboard_metrics()
            app.logger.info(f"📊 Daily PSU dashboard snapshot: {metrics}")

    scheduler.start()
    app.logger.info("🕒 Scheduler initialized successfully.")

    # -----------------------------------------------------------------
    # Security & Request Enhancements
    # -----------------------------------------------------------------
    @app.before_request
    def secure_headers():
        """Set security and performance headers."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "no-referrer-when-downgrade",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        for k, v in headers.items():
            request.headers[k] = v

    @app.after_request
    def add_caching_headers(response):
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    # -----------------------------------------------------------------
    # Error Handlers
    # -----------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Not Found: {request.path}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 Error: {e}")
        try:
            send_system_alert("Internal Server Error", str(e))
        except Exception:
            pass
        return render_template("errors/500.html"), 500

    # -----------------------------------------------------------------
    # Request Loader (for API Tokens)
    # -----------------------------------------------------------------
    from flask_login import LoginManager
    from models import User

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.request_loader
    def load_user_from_request(request):
        """Allows API calls via Authorization header token."""
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token_value = token.split(" ")[1]
            user = User.verify_auth_token(token_value)
            if user:
                return user
        return None

    # -----------------------------------------------------------------
    # Root route (fallback)
    # -----------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("core/home.html")

    return app


# ---------------------------------------------------------------------
# Production Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
