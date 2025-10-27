"""
PittState-Connect | Production Entry Point
Main application factory for Render deployment.
Initializes all blueprints, logging, analytics, and PSU modules.
"""

import os
from loguru import logger
from flask import Flask, jsonify
from extensions import (
    db,
    mail,
    migrate,
    login_manager,
    cache,
    limiter,
    scheduler,
    redis_client,
    init_extensions,
)
from config import load_config
from openai import OpenAI

# ======================================================
# 🧩 APP FACTORY
# ======================================================
def create_app():
    app = Flask(__name__)

    # Load Production Config
    load_config(app)
    init_extensions(app)

    logger.info("🦍 PittState-Connect configuration applied successfully.")

    # Register blueprints safely
    register_blueprints(app)
    register_error_handlers(app)
    register_health_routes(app)

    return app


# ======================================================
# 🧩 BLUEPRINT REGISTRATION
# ======================================================
def register_blueprints(app):
    from importlib import import_module

    blueprints = [
        "blueprints.admin.routes",
        "blueprints.auth.routes",
        "blueprints.core.routes",
        "blueprints.analytics.routes",
        "blueprints.api.routes",
        "blueprints.connections.routes",
        "blueprints.departments.routes",
        "blueprints.events.routes",
        "blueprints.faculty.routes",
        "blueprints.feed.routes",
        "blueprints.groups.routes",
        "blueprints.notifications.routes",
        "blueprints.profile.routes",
        "blueprints.scholarships.routes",
        "blueprints.stories.routes",
    ]

    for bp in blueprints:
        try:
            mod = import_module(bp)
            app.register_blueprint(mod.bp)
            logger.info(f"✅ Registered blueprint: {bp}")
        except Exception as e:
            logger.error(f"❌ Failed to register blueprint {bp}: {e}")


# ======================================================
# ❤️ HEALTH & AI CHECKS
# ======================================================
def register_health_routes(app):
    @app.route("/health")
    def health():
        return jsonify(status="ok", env=app.config.get("ENV", "production"))

    @app.route("/ai/ping")
    def ai_ping():
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                return jsonify(ai_status="missing_key"), 400

            client = OpenAI(api_key=api_key)
            response = client.responses.create(model="gpt-4o-mini", input="ping")
            return jsonify(ai_status="ok", output=response.output_text)
        except Exception as e:
            return jsonify(ai_status="error", message=str(e)), 500


# ======================================================
# 🧱 ERROR HANDLERS
# ======================================================
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return (
            jsonify(error="Page not found", status=404),
            404,
        )

    @app.errorhandler(500)
    def server_error(e):
        return (
            jsonify(error="Internal server error", status=500),
            500,
        )

    logger.info("✅ PSU error handlers registered successfully.")


# ======================================================
# 🚀 APP ENTRY
# ======================================================
app = create_app()
logger.info("🦍 PittState-Connect Flask app created successfully.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
