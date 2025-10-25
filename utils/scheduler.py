# utils/scheduler_util.py
# ---------------------------------------------------------------------
# PSU Scheduler Utility
# Provides health checks, analytics syncing, and alert monitoring
# for PittState-Connect background jobs.
# ---------------------------------------------------------------------

from datetime import datetime, timedelta
from extensions import redis_client
from utils.mail_util import send_system_alert
import json
import logging


def monitor_scheduler_health(app):
    """
    Check the scheduler's runtime heartbeat and trigger alerts
    if a background job has not reported recently.
    """
    try:
        key = "scheduler:last_check"
        now = datetime.utcnow()

        # Retrieve previous timestamp
        last_check_raw = redis_client.get(key)
        if last_check_raw:
            last_check = datetime.fromisoformat(last_check_raw.decode("utf-8"))
            delta = now - last_check
            if delta > timedelta(hours=3):
                msg = f"Scheduler heartbeat delay: {delta.total_seconds()/3600:.2f} hours."
                app.logger.warning(msg)
                send_system_alert("⚠️ Scheduler Health Alert", msg)
        else:
            app.logger.info("🕒 Initial scheduler health check created.")

        # Update current timestamp
        redis_client.set(key, now.isoformat())
        app.logger.info(f"[Scheduler Health] OK @ {now.isoformat()}")

    except Exception as e:
        app.logger.error(f"[Scheduler Health] Failed: {e}")
        try:
            send_system_alert("Scheduler Health Error", str(e))
        except Exception:
            pass


def log_job_status(job_name: str, success: bool, message: str = ""):
    """
    Log and cache job status updates for analytics monitoring.
    """
    try:
        status_entry = {
            "job": job_name,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "message": message
        }
        redis_client.lpush("scheduler:job_history", json.dumps(status_entry))
        redis_client.ltrim("scheduler:job_history", 0, 49)  # Keep last 50 jobs
        logging.info(f"🧭 Job {job_name}: {'✅' if success else '❌'} {message}")
    except Exception as e:
        logging.error(f"[Scheduler Job Log] Error: {e}")
