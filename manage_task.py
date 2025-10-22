# =============================================================
# FILE: manage_tasks.py
# PittState-Connect — Advanced Scheduled / Cron Task Manager
# -------------------------------------------------------------
# Runs daily / weekly jobs for:
#   - Scholarship reminders
#   - Donor analytics + dashboards
#   - Mentor digests
#   - Financial dashboards
#   - Temp data cleanup
# Optional: integrates with Sentry + advanced logging.
# =============================================================

import os
import logging
import time
from datetime import datetime, timedelta

from app_pro import create_app
from models import db
from utils.mail_util import send_email
from worker import (
    send_scholarship_reminder,
    sync_donor_analytics,
    generate_weekly_mentor_digest,
    refresh_financial_aid_dashboard,
)

# -------------------------------------------------------------
# Optional integrations
# -------------------------------------------------------------
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    SENTRY_ENABLED = True
except ImportError:
    SENTRY_ENABLED = False

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------
app = create_app()
app.app_context().push()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | scheduler | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scheduler")

if SENTRY_ENABLED and os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("FLASK_ENV", "production"),
    )
    log.info("🧩 Sentry monitoring enabled for scheduled tasks.")
else:
    log.info("Sentry disabled or DSN missing.")

# -------------------------------------------------------------
# JOB REGISTRY (tasks to run)
# -------------------------------------------------------------
def run_scholarship_reminders():
    """Notify students about upcoming scholarship deadlines."""
    log.info("📅 Checking scholarships due soon...")
    # TODO: Replace with real database query
    upcoming = [
        {
            "email": "student@pittstate.edu",
            "name": "Future Leaders Grant",
            "deadline": "2025-10-25",
        }
    ]
    for s in upcoming:
        send_scholarship_reminder(s["email"], s["name"], s["deadline"])
    log.info("✅ Scholarship reminders complete.")


def run_donor_analytics_sync():
    """Refresh donor impact and funding dashboards."""
    log.info("📈 Syncing donor analytics...")
    sync_donor_analytics()
    log.info("✅ Donor analytics sync done.")


def run_financial_dashboards_refresh():
    """Recalculate funding progress and cost-to-completion stats."""
    log.info("💰 Refreshing financial aid dashboards...")
    refresh_financial_aid_dashboard()
    log.info("✅ Financial dashboards updated.")


def run_mentor_weekly_digest():
    """Send mentor engagement digests (Fridays only)."""
    today = datetime.utcnow()
    if today.weekday() == 4:
        log.info("📬 Friday detected — sending mentor digest...")
        generate_weekly_mentor_digest()
        log.info("✅ Mentor digest sent.")
    else:
        log.info("⏭️ Not Friday (%s) — skipping mentor digest.", today.strftime("%A"))


def cleanup_temp_data():
    """Delete old temporary or analytic log data."""
    log.info("🧹 Cleaning up temporary analytics data...")
    # Example future logic:
    # db.session.query(TempAnalytics).filter(TempAnalytics.created_at < cutoff).delete()
    db.session.commit()
    log.info("✅ Temp data cleanup complete.")


# -------------------------------------------------------------
# METRICS AND EXECUTION WRAPPER
# -------------------------------------------------------------
def execute_with_metrics(task_func, task_name: str):
    """Wraps tasks with timing and error handling."""
    start = datetime.utcnow()
    try:
        task_func()
        duration = (datetime.utcnow() - start).total_seconds()
        log.info("⏱️ %s completed in %.2fs", task_name, duration)
    except Exception as e:
        log.exception("❌ Task %s failed: %s", task_name, e)
        if SENTRY_ENABLED:
            sentry_sdk.capture_exception(e)
    finally:
        db.session.remove()  # ensure clean DB state


# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    log.info("🕒 Starting scheduled maintenance cycle at %s", datetime.utcnow())
    try:
        # ✅ Task sequence
        execute_with_metrics(run_scholarship_reminders, "Scholarship Reminders")
        execute_with_metrics(run_donor_analytics_sync, "Donor Analytics Sync")
        execute_with_metrics(run_financial_dashboards_refresh, "Financial Dashboards")
        execute_with_metrics(run_mentor_weekly_digest, "Mentor Weekly Digest")
        execute_with_metrics(cleanup_temp_data, "Temp Data Cleanup")

        log.info("✅ All scheduled jobs completed successfully.")
    except Exception as e:
        log.exception("❌ Scheduler runtime error: %s", e)
        if SENTRY_ENABLED:
            sentry_sdk.capture_exception(e)
    finally:
        log.info("🏁 Scheduled maintenance cycle finished at %s", datetime.utcnow())
        time.sleep(1)  # safe exit delay for Render Cron
