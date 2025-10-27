#!/usr/bin/env python3
"""
tools/run_scheduler.py
-------------------------------------------------------------
PittState-Connect APScheduler runner (production ready)
-------------------------------------------------------------
• Boots Flask app context
• Enqueues Redis tasks for worker.py
• Manages scholarships, AI Smart-Match, cache warming, analytics
• Supports flexible CRON intervals via env vars
• Includes heartbeat, metrics, and graceful shutdown
• Colorized structured logging (loguru)
"""

import os
import sys
import signal
import time
import json
from datetime import datetime, timezone
from loguru import logger

# ---------------------------------------------------------------------------
# Flask app import
# ---------------------------------------------------------------------------
try:
    from app_pro import app
except Exception as e:
    print(f"[scheduler] FATAL: cannot import app_pro.app: {e}", file=sys.stderr)
    raise

# ---------------------------------------------------------------------------
# Redis + Extensions (fallback-safe)
# ---------------------------------------------------------------------------
def get_redis():
    try:
        from extensions import redis_client as shared
        if shared:
            return shared
    except Exception:
        pass

    url = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("Redis init failed: {}", e)
        return None


redis_client = get_redis()

MAIL_QUEUE_KEY = os.getenv("MAIL_QUEUE_KEY", "queue:mail")
AI_QUEUE_KEY = os.getenv("AI_QUEUE_KEY", "queue:ai")
HEARTBEAT_KEY = os.getenv("SCHED_HEARTBEAT_KEY", "scheduler:heartbeat")
METRICS_KEY = os.getenv("SCHED_METRICS_KEY", "scheduler:metrics")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, enqueue=True, colorize=True)

RUNNING = True


def utc_now():
    return datetime.now(timezone.utc)


def heartbeat():
    if not redis_client:
        return
    try:
        redis_client.hset(
            HEARTBEAT_KEY,
            mapping={
                "ts": utc_now().isoformat(),
                "pid": os.getpid(),
                "log": LOG_LEVEL,
                "ver": "1.0.0",
            },
        )
        redis_client.expire(HEARTBEAT_KEY, 180)
    except Exception as e:
        logger.debug("Scheduler heartbeat failed: {}", e)


def metric(name, count=1):
    if not redis_client:
        return
    try:
        redis_client.hincrby(METRICS_KEY, name, count)
        redis_client.expire(METRICS_KEY, 86400)
    except Exception as e:
        logger.debug("Metric error: {}", e)


def enqueue(queue_key, payload):
    if not redis_client:
        logger.warning("Redis not available; skipping enqueue -> {}", payload)
        return False
    try:
        redis_client.lpush(queue_key, json.dumps(payload))
        return True
    except Exception as e:
        logger.error("Enqueue failed: {}", e)
        return False


# ---------------------------------------------------------------------------
# Job Definitions
# ---------------------------------------------------------------------------
def job_cache_warm_all():
    logger.info("🧊 Cache warm job triggered")
    ok = enqueue(AI_QUEUE_KEY, {"type": "cache_warm_all"})
    metric("jobs.cache_warm_all", 1 if ok else 0)


def job_scholarship_deadline_reminders():
    logger.info("📅 Scholarship reminder job triggered")
    payload = {
        "type": "scholarship_deadline_reminder",
        "subject": "Scholarship Deadline Reminder",
        "html": "<p>Stay on track — your scholarship deadlines are approaching!</p>",
    }
    ok = enqueue(MAIL_QUEUE_KEY, payload)
    metric("jobs.scholarship_reminder", 1 if ok else 0)


def job_daily_digest():
    logger.info("📧 Daily digest job triggered")
    sender = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")
    recipient = os.getenv("DIGEST_TO_EMAIL", "")
    if not recipient:
        logger.warning("DIGEST_TO_EMAIL not set; skipping daily digest")
        return
    html = "<p>Your daily PittState-Connect digest is ready.</p>"
    ok = enqueue(MAIL_QUEUE_KEY, {"to": recipient, "subject": "Daily Digest", "html": html, "sender": sender})
    metric("jobs.daily_digest", 1 if ok else 0)


def job_smartmatch_refresh():
    logger.info("🧠 Smart-Match AI refresh triggered")
    ok = enqueue(AI_QUEUE_KEY, {"type": "smart_match_train", "dataset": "auto_refresh"})
    metric("jobs.smartmatch_refresh", 1 if ok else 0)


def job_analytics_refresh():
    logger.info("📊 Analytics cache refresh triggered")
    ok = enqueue(AI_QUEUE_KEY, {"type": "analytics_refresh"})
    metric("jobs.analytics_refresh", 1 if ok else 0)


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------
def setup_signal_handlers(sched):
    def graceful(signum, frame):
        global RUNNING
        logger.warning("Signal {} received — shutting down scheduler", signum)
        RUNNING = False
        try:
            sched.shutdown(wait=False)
        except Exception:
            pass

    signal.signal(signal.SIGINT, graceful)
    signal.signal(signal.SIGTERM, graceful)


def register_jobs(sched):
    cron_jobs = {
        "cache_warm_all": ("*/30 * * * *", job_cache_warm_all),
        "daily_digest": ("0 7 * * *", job_daily_digest),
        "scholarship_reminders": ("15 12 * * *", job_scholarship_deadline_reminders),
        "smartmatch_refresh": ("0 * * * *", job_smartmatch_refresh),
        "analytics_refresh": ("*/20 * * * *", job_analytics_refresh),
    }

    for job_id, (cron, func) in cron_jobs.items():
        try:
            m, h, d, mo, dow = cron.split()
            sched.add_job(
                func=func,
                trigger="cron",
                id=job_id,
                minute=m, hour=h, day=d, month=mo, day_of_week=dow,
                replace_existing=True, max_instances=1, coalesce=True,
            )
            logger.info("Registered job '{}' ({})", job_id, cron)
        except Exception as e:
            logger.error("Failed to register job '{}': {}", job_id, e)


def main():
    from apscheduler.schedulers.background import BackgroundScheduler

    logger.info("🚀 Starting PittState-Connect Scheduler…")
    sched = BackgroundScheduler(timezone="America/Chicago")
    register_jobs(sched)
    setup_signal_handlers(sched)

    with app.app_context():
        sched.start()
        logger.success("Scheduler started with jobs: {}", [j.id for j in sched.get_jobs()])

        while RUNNING:
            heartbeat()
            time.sleep(3)

    logger.info("Scheduler shutdown complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
