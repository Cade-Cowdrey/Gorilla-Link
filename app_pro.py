import os
from flask import Flask, render_template, jsonify, url_for
from extensions import db, cache, migrate, mail, scheduler, login_manager
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from logging.config import dictConfig

# ============================================================
# 🔰 Logging Configuration
# ============================================================
dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}},
    "handlers": {"wsgi": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "default"}},
    "root": {"level": "INFO", "handlers": ["wsgi"]}
})

# ============================================================
# 🏗️ App Factory
# ============================================================
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app)

# ============================================================
# ⚙️ Extensions Initialization
# ============================================================
db.init_app(app)
cache.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
scheduler.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth_bp.login"
scheduler.start()

# ============================================================
# 🧩 Error Handling Helpers
# ============================================================
@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"[404] {e}")
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"[500] {e}")
    return render_template("errors/500.html"), 500

# ============================================================
# ✅ Safe URL helper
# ============================================================
def safe_url_for(endpoint_name, **values):
    try:
        return url_for(endpoint_name, **values)
    except Exception as e:
        app.logger.warning(f"[safe_url_for] Failed for {endpoint_name}: {e}")
        return "#"

app.jinja_env.globals["safe_url_for"] = safe_url_for

# ============================================================
# 📦 Blueprint Imports
# ============================================================
from blueprints.core.routes import core_bp
from blueprints.departments.routes import departments_bp
from blueprints.careers.routes import careers_bp
from blueprints.scholarships.routes import scholarships_bp
from blueprints.analytics.routes import analytics_bp
from blueprints.faculty.routes import faculty_bp

# ============================================================
# 🧩 Register Blueprints
# ============================================================
app.register_blueprint(core_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(careers_bp)
app.register_blueprint(scholarships_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(faculty_bp)

# ============================================================
# 🔒 Health & readiness endpoints
# ============================================================
@app.route("/healthz")
def healthz():
    return jsonify(status="ok", service="PittState-Connect"), 200

@app.route("/readiness")
def readiness():
    try:
        db.session.execute("SELECT 1")
        return jsonify(status="ready"), 200
    except Exception as e:
        app.logger.error(f"DB readiness failed: {e}")
        return jsonify(status="unready"), 500

# ============================================================
# 🏁 Startup Banner
# ============================================================
with app.app_context():
    app.logger.info("[INIT] PittState-Connect started in production mode.")
    app.logger.info("✅ All extensions initialized successfully.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
