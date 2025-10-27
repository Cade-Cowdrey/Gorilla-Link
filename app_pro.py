"""
PittState-Connect | Production Entry Point
This file bootstraps the Flask application for Render deployment.
It auto-detects environment configuration, initializes all extensions,
registers blueprints, sets up global error handling, and starts the app.
"""

import os
from loguru import logger
from flask import Flask, render_template, redirect, url_for, jsonify
from config import load_config
from extensions import init_extensions, db, scheduler
from datetime import datetime

# ======================================================
# ⚙️ APP FACTORY
# ======================================================
def create_app():
    """Create and configure the Flask application instance."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load configuration dynamically (production/dev/test)
    load_config(app)

    # Initialize all extensions (db, redis, limiter, csrf, etc.)
    init_extensions(app)

    # Register blueprints automatically
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Maintenance mode check
    if app.config.get("MAINTENANCE_MODE", False):
        logger.warning("🚧 App running in maintenance mode.")
        @app.before_request
        def maintenance_check():
            return render_template("errors/maintenance.html"), 503

    logger.info("🦍 PittState-Connect Flask app created successfully.")
    return app


# ======================================================
# 📦 BLUEPRINT AUTO-LOADER
# ======================================================
def register_blueprints(app):
    """Auto-detect and register all blueprints from the blueprints folder."""
    import importlib
    import pkgutil

    blueprint_dir = "blueprints"
    for _, module_name, _ in pkgutil.iter_modules([blueprint_dir]):
        try:
            module = importlib.import_module(f"{blueprint_dir}.{module_name}.routes")
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
                logger.info(f"🧩 Registered blueprint: {module_name}")
        except Exception as e:
            logger.error(f"❌ Failed to register blueprint {module_name}: {e}")


# ======================================================
# ❌ GLOBAL ERROR HANDLERS
# ======================================================
def register_error_handlers(app):
    """Attach PSU-branded error templates for common HTTP errors."""

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"⚠️ 404 Not Found: {error}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"🚫 403 Forbidden: {error}")
        return render_template("errors/403.html"), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.warning(f"🔐 401 Unauthorized: {error}")
        return render_template("errors/401.html"), 401

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"💥 500 Internal Server Error: {error}")
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def rate_limit_error(error):
        logger.warning(f"⏳ 429 Too Many Requests: {error}")
        return render_template("errors/429.html"), 429

    logger.info("✅ PSU error handlers registered successfully.")


# ======================================================
# 🧠 HEALTH CHECK + AI ROUTES (optional enhancements)
# ======================================================
def register_health_routes(app):
    """Simple internal API routes for diagnostics and AI endpoint."""

    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "time": datetime.utcnow().isoformat(),
            "analytics_enabled": app.config.get("ENABLE_ANALYTICS"),
            "ai_assistant_enabled": app.config.get("ENABLE_AI_ASSISTANT"),
        }), 200

    if app.config.get("ENABLE_AI_ASSISTANT"):
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        
        @app.route("/ai/ask", methods=["POST"])
        def ai_assistant():
            from flask import request
            query = request.json.get("query", "")
            if not query:
                return jsonify({"error": "Missing query"}), 400
            try:
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": query}],
                )
                answer = completion.choices[0].message.content
                return jsonify({"response": answer})
            except Exception as e:
                logger.error(f"🤖 AI Assistant error: {e}")
                return jsonify({"error": str(e)}), 500


# ======================================================
# 🚀 APP INITIALIZATION
# ======================================================
app = create_app()
register_health_routes(app)

logger.info(f"🚀 PittState-Connect launching in {app.config.get('ENV', 'production').title()} mode.")
logger.info(f"🗄️  Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
logger.info(f"🕒 Scheduler active: {scheduler.running}")
logger.info("✅ Application startup complete.")

# ======================================================
# 🔥 WSGI Entry Point
# ======================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
