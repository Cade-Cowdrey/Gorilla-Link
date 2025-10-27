import os
import logging
from flask import Flask, jsonify
from config.config_production import ConfigProduction
from extensions import init_extensions, scheduler
from utils.analytics_util import track_page_view
from openai import OpenAI

def create_app():
    app = Flask(__name__)
    app.config.from_object(ConfigProduction)

    # Initialize all extensions
    init_extensions(app)

    # Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    logging.info("🦍 PittState-Connect configuration applied successfully.")

    # Register blueprints dynamically
    from blueprints import register_blueprints
    register_blueprints(app)

    # Health route
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "env": "production"}), 200

    # OpenAI test route (optional)
    @app.route("/ai/test")
    def ai_test():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        return jsonify({"ok": True, "message": "AI assistant operational"})

    # Background job example
    @scheduler.task("cron", id="nightly_job", hour=2)
    def nightly_job():
        logging.info("🌙 Running nightly scheduled job...")

    return app


# Gunicorn entrypoint
app = create_app()
