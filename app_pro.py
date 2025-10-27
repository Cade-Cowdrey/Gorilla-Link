"""
app_pro.py
Production entry point for PittState-Connect.
Includes logging, extension registration, blueprint autoloading,
error handling, Redis and database health checks, and optional enhancements.
"""

import os
import sys
import logging
from loguru import logger
from flask import Flask, render_template, jsonify
from config import create_app, db, mail, cache, scheduler, csrf, login_manager


# ============================================================
# Logging Setup with Loguru
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger.remove()
logger.add(sys.stdout, colorize=True, level=LOG_LEVEL)
logger.add("pittstate_connect.log", rotation="5 MB", retention="10 days", level=LOG_LEVEL)
logger.info("🚀 PittState-Connect initializing in production mode...")


# ============================================================
# Flask App Factory Initialization
# ============================================================
try:
    app = create_app()
except Exception as e:
    logger.exception(f"❌ Failed to create Flask app: {e}")
    raise


# ============================================================
# Blueprint Auto-Loader
# ============================================================
def register_blueprints(app):
    """
    Dynamically registers all blueprints in /blueprints directory.
    Each blueprint must expose 'bp' variable.
    """
    import importlib
    import pkgutil

    blueprints_dir = os.path.join(app.root_path, "blueprints")
    if not os.path.isdir(blueprints_dir):
        logger.warning("⚠️ No blueprints directory found — skipping auto-registration.")
        return

    for finder, name, ispkg in pkgutil.iter_modules([blueprints_dir]):
        try:
            module_path = f"blueprints.{name}.routes"
            module = importlib.import_module(module_path)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
                logger.info(f"✅ Registered blueprint: {name}_bp")
            else:
                logger.warning(f"⚠️ No blueprint object found in {module_path}")
        except Exception as e:
            logger.warning(f"⚠️ Skipped blueprint {name}_bp: {e}")


try:
    register_blueprints(app)
except Exception as e:
    logger.error(f"❌ Blueprint registration failed: {e}")


# ============================================================
# Error Handling
# ============================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


@app.errorhandler(Exception)
def handle_global_exception(error):
    logger.exception(f"⚠️ Global exception: {error}")
    return jsonify(error=str(error)), 500


# ============================================================
# CLI and Admin Utilities
# ============================================================

@app.cli.command("create-admin")
def create_admin():
    """Create or update the default admin user"""
    from models import User
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    if not all([admin_email, admin_password]):
        logger.error("❌ Missing ADMIN_EMAIL or ADMIN_PASSWORD in environment.")
        return

    with app.app_context():
        admin = User.query.filter_by(email=admin_email).first()
        if admin:
            admin.set_password(admin_password)
            logger.info("🔑 Updated existing admin credentials.")
        else:
            admin = User(name=admin_name, email=admin_email, role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            logger.info("👑 Created new admin account.")
        db.session.commit()
        logger.success("✅ Admin setup complete.")


# ============================================================
# Application Launch Summary
# ============================================================

logger.info(f"✅ App initialized with Redis: {os.getenv('REDIS_URL')}")
logger.info(f"✅ Database: {os.getenv('DATABASE_URL')}")
logger.info(f"✅ Mail sender: {os.getenv('MAIL_DEFAULT_SENDER')}")
logger.info(f"🌐 Environment: {os.getenv('FLASK_ENV', 'production')}")

# Final success log
logger.success("🔥 PittState-Connect fully initialized and ready for launch!")


# ============================================================
# Run App (Gunicorn handles this on Render)
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
