"""
PittState-Connect | Background Worker
Handles background tasks, async jobs, and nightly maintenance routines.
Integrated with Flask app context, Redis queue, and APScheduler.
"""

import os
import time
from loguru import logger
from datetime import datetime
from flask import Flask
from config import load_config
from extensions import (
    db,
    mail,
    redis_client,
    scheduler,
    cache,
    init_extensions,
)
from flask_mail import Message

# ======================================================
# ⚙️ APP SETUP (HEADLESS WORKER CONTEXT)
# ======================================================
def create_worker_app():
    """Create an app instance for running async or scheduled tasks."""
    app = Flask(__name__)
    load_config(app)
    init_extensions(app)
    return app


app = create_worker_app()
logger.info("🦍 PittState-Connect background worker initialized successfully.")


# ======================================================
# 📬 EMAIL DISPATCHER
# ======================================================
def send_email(subject, recipients, body, html=None):
    """Send an email asynchronously via the Flask-Mail extension."""
    with app.app_context():
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body,
                html=html,
                sender=app.config.get("MAIL_DEFAULT_SENDER"),
            )
            mail.send(msg)
            logger.info(f"📧 Email sent successfully to {recipients}")
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")


def process_email_queue():
    """Check Redis for queued emails and send them."""
    if not redis_client:
        logger.warning("⚠️ Redis not connected — skipping email queue processing.")
        return
    try:
        while True:
            task = redis_client.lpop("email_queue")
            if task:
                import json
                email_data = json.loads(task)
                send_email(
                    subject=email_data["subject"],
                    recipients=email_data["recipients"],
                    body=email_data["body"],
                    html=email_data.get("html", None),
                )
            else:
                time.sleep(5)  # No emails, check again
    except Exception as e:
        logger.error(f"💥 Email queue processor crashed: {e}")


# ======================================================
# 🌙 EXTENDED NIGHTLY JOBS
# ======================================================
def nightly_maintenance():
    """Run full nightly maintenance tasks: analytics refresh, cache clear, report summaries."""
    with app.app_context():
        try:
            logger.info("🌙 Running nightly maintenance job...")
            
            # Example 1: Flush Redis Cache
            if redis_client:
                redis_client.delete("analytics_summary")
                redis_client.delete("leaderboard_cache")
                logger.info("♻️ Redis analytics and leaderboard caches cleared.")

            # Example 2: Email Admin summary report
            admin_email = app.config.get("ADMIN_EMAIL")
            if admin_email:
                send_email(
                    subject="🌙 PittState-Connect Nightly Report",
                    recipients=[admin_email],
                    body=f"Nightly maintenance completed successfully at {datetime.utcnow()} UTC.",
                )

            # Example 3: Placeholder for analytics recomputation
            # from utils.analytics import refresh_analytics
            # refresh_analytics()

            logger.info("✅ Nightly maintenance routine finished.")
        except Exception as e:
            logger.error(f"❌ Nightly maintenance failed: {e}")


# ======================================================
# 🔁 SCHEDULER SETUP
# ======================================================
def register_background_jobs():
    """Register worker-specific scheduled jobs."""
    scheduler.add_job(
        id="email_queue_processor",
        func=process_email_queue,
        trigger="interval",
        seconds=15,
    )

    scheduler.add_job(
        id="nightly_maintenance",
        func=nightly_maintenance,
        trigger="cron",
        hour=2,
        minute=0,
        timezone="US/Central",
    )

    logger.info("✅ Background worker jobs registered successfully.")


# ======================================================
# 🚀 MAIN EXECUTION LOOP
# ======================================================
if __name__ == "__main__":
    register_background_jobs()
    logger.info("🧩 Worker scheduler started. Running background loops...")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        logger.warning("🛑 Worker manually stopped.")
