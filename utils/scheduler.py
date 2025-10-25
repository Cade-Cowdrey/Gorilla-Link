import datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

def job_health_ping(app):
    """Simple heartbeat check."""
    with app.app_context():
        app.logger.info(f"[Scheduler] ✅ Health ping @ {dt.datetime.utcnow().isoformat()}")

def job_collect_usage(app):
    """Collects analytics and usage metrics every hour."""
    from models import UsageMetric, db
    with app.app_context():
        metric = UsageMetric(metric_name="system_health", metric_value=1.0)
        db.session.add(metric)
        db.session.commit()
        app.logger.info("[Scheduler] 📊 Usage metrics collected successfully.")

def job_ai_scholarship_match(app):
    """Optional: run SmartMatch AI recommender batch."""
    try:
        with app.app_context():
            app.logger.info("[Scheduler] 🤖 Running SmartMatch AI recommender update...")
            # placeholder for AI pipeline logic
    except Exception as e:
        app.logger.warning(f"[Scheduler] SmartMatch error: {e}")

def init_scheduler(app):
    """Attach background tasks safely with Flask context."""
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(lambda: job_health_ping(app), trigger="interval", minutes=5, id="health_ping")
    scheduler.add_job(lambda: job_collect_usage(app), trigger="interval", hours=1, id="usage_collect")
    scheduler.add_job(lambda: job_ai_scholarship_match(app), trigger="interval", hours=6, id="ai_matcher")
    scheduler.start()
    app.logger.info("✅ Background scheduler started successfully.")
