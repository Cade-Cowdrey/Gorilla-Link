# =============================================================
# FILE: manage_tasks.py
# PittState-Connect — Scheduled / Cron Tasks
# Runs daily or weekly jobs for analytics, scholarships,
# donor updates, mentor digests, and data cleanup.
# =============================================================

import os
import logging
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

app = create_app()
app.app_context().push()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scheduler")

# -------------------------------------------------------------
# SCHOLARSHIP REMINDERS
# -------------------------------------------------------------
def run_scholarship_reminders():
    """Check scholarships due within 3 days and notify students."""
    log.info("📅 Checking scholarships due soon...")
    # Placeholder for real query
    upcoming = [
        {"email": "student@pittstate.edu", "name": "Future Leaders Grant", "deadline": "2025-10-25"}
    ]
    for s in upcoming:
        send_scholarship_reminder(s["email"], s["name"], s["deadline"])
    log.info("✅ Scholarship reminders complete.")


# -------------------------------------------------------------
# DONOR / FINANCIAL DATA UPDATES
# -------------------------------------------------------------
def run_donor_analytics_sync():
    log.info("📈 Running donor analytics sync...")
    sync_donor_analytics()


def run_financial_dashboards_refresh():
    log.info("💰 Refreshing financial aid dashboards...")
    refresh_financial_aid_dashboard()


# -------------------------------------------------------------
# MENTOR / COMMUNITY UPDATES
# -------------------------------------------------------------
def run_mentor_weekly_digest():
    """Send mentors weekly summaries on Fridays."""
    today = datetime.utcnow()
    if today.weekday() == 4:
        generate_weekly_mentor_digest()
        log.info("✅ Mentor digest sent.")
    else:
        log.info("⏭️ Not Friday — skipping mentor digest.")


# -------------------------------------------------------------
# CLEANUP / ANALYTICS
# -------------------------------------------------------------
def cleanup_temp_data():
    """Delete old temporary records or analytics logs."""
    log.info("🧹 Cleaning up temporary analytics data...")
    # Example: db.session.query(TempAnalytics).delete()
    db.session.commit()
    log.info("✅ Temp data cleanup complete.")


# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    log.info("🕒 Starting scheduled maintenance cycle at %s", datetime.utcnow())
    try:
        run_scholarship_reminders()
        run_donor_analytics_sync()
        run_financial_dashboards_refresh()
        run_mentor_weekly_digest()
        cleanup_temp_data()
    except Exception as e:
        log.error("❌ Task scheduler error: %s", e)
    finally:
        log.info("✅ Scheduled maintenance finished.")
