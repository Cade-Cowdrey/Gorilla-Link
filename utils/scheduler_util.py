# utils/scheduler_util.py
# ---------------------------------------------------------------------
# PSU Scheduler Utility (Production-Ready)
# ---------------------------------------------------------------------
# Provides background job health checks, analytics sync monitoring,
# retry logic, alert escalation, and Redis-integrated logging for
# the PittState-Connect platform.
# ---------------------------------------------------------------------

import json
import logging
from datetime import datetime, timedelta
from random import randint

from extensions import redis_client, db
from utils.mail_util import send_system_alert


def _redis_safe_get(key: str):
    try:
        return redis_client.get(key)
    except Exception as e:
        logging.warning(f"[SchedulerUtil] Redis get failed: {e}")
        return None


def _redis_safe_set(key: str, value, ex=None):
    try:
        redis_client.set(key, value, ex=ex)
    except Exception as e:
        logging.warning(f"[SchedulerUtil] Redis set failed: {e}")


# ---------------------------------------------------------------------
# Scheduler Health Monitor
# ---------------------------------------------------------------------
def monitor_scheduler_health(app):
    """
    Checks scheduler heartbeat and triggers PSU system alerts if lag exceeds threshold.
    """
    try:
        now = datetime.utcnow()
        key = "scheduler:last_check"
        last_check_raw = _redis_safe_get(key)

        if last_check_raw:
            last_check = datetime.fromisoformat(last_check_raw.decode("utf-8"))
            delta = now - last_check
            if delta > timedelta(hours=3):
                msg = (
                    f"⚠️ PSU Scheduler Delay Detected!\n\n"
                    f"Last heartbeat: {last_check.isoformat()}\n"
                    f"Delay: {delta.total_seconds()/3600:.2f} hours.\n\n"
                    "Immediate investigation recommended."
                )
                app.logger.warning(msg)
                send_system_alert("⚠️ Scheduler Health Alert", msg)
        else:
            app.logger.info("🕒 Initial scheduler health check established.")

        _redis_safe_set(key, now.isoformat())
        app.logger.info(f"✅ Scheduler heartbeat OK @ {now.isoformat()}")

    except Exception as e:
        app.logger.error(f"[Scheduler Health] Failed: {e}")
        try:
            send_system_alert("Scheduler Health Error", str(e))
        except Exception as alert_err:
            app.logger.error(f"Failed to send alert: {alert_err}")


# ---------------------------------------------------------------------
# Job Status Tracking
# ---------------------------------------------------------------------
def log_job_status(job_name: str, success: bool, message: str = "", duration: float = 0.0):
    """
    Logs job execution status and stores in Redis for dashboard visibility.
    Automatically escalates if job fails repeatedly.
    """
    try:
        now = datetime.utcnow().isoformat()
        entry = {
            "job": job_name,
            "timestamp": now,
            "success": success,
            "message": message or ("Completed successfully" if success else "Job failed"),
            "duration": round(duration, 2),
        }

        # Push to Redis job history
        _redis_safe_set(f"scheduler:job:{job_name}:last", json.dumps(entry))
        redis_client.lpush("scheduler:job_history", json.dumps(entry))
        redis_client.ltrim("scheduler:job_history", 0, 99)  # Keep last 100 jobs

        logging.info(f"🧭 Job [{job_name}] {'✅ Success' if success else '❌ Failure'} | {message}")

        # Track failures for escalation
        if not success:
            _track_failures(job_name, entry)

    except Exception as e:
        logging.error(f"[Scheduler Job Log] Error: {e}")


def _track_failures(job_name: str, entry: dict):
    """
    Tracks consecutive job failures and escalates after threshold.
    """
    try:
        fail_key = f"scheduler:failcount:{job_name}"
        current_fails = redis_client.incr(fail_key)
        redis_client.expire(fail_key, 86400)  # reset every 24 hours

        if current_fails >= 3:  # type: ignore[operator]
            msg = (
                f"🚨 PSU Scheduler Alert: Job '{job_name}' failed {current_fails} times in 24h.\n\n"
                f"Last error: {entry.get('message', 'No message')}\n"
                f"Timestamp: {entry.get('timestamp')}\n\n"
                "System will attempt auto-recovery and notify analytics dashboard."
            )
            send_system_alert("🚨 Repeated Job Failures", msg)
            logging.warning(msg)
    except Exception as e:
        logging.error(f"[Scheduler Failure Tracking] {e}")


# ---------------------------------------------------------------------
# Analytics Job Mock / Sample Generator
# ---------------------------------------------------------------------
def simulate_analytics_job():
    """
    Simulates a PSU analytics sync job for testing.
    """
    job_name = "analytics_sync"
    try:
        start = datetime.utcnow()
        # Simulate variable duration
        duration = randint(1, 5)
        # Random success/failure simulation for monitoring
        if randint(1, 10) > 2:
            log_job_status(job_name, True, "Analytics sync successful.", duration)
        else:
            raise RuntimeError("Simulated analytics sync error.")
    except Exception as e:
        log_job_status(job_name, False, str(e))
        raise
