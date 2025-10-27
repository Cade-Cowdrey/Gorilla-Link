#!/usr/bin/env python3
"""
Central APScheduler runner for PittState-Connect.

Enhancements:
- Boots your Flask app context (imports app_pro.app)
- Registers robust cron/interval jobs (env-configurable)
- Enqueues work to Redis (so your worker.py does the heavy lifting)
- Heartbeat + metrics in Redis (optional)
- Graceful shutdown via SIGINT/SIGTERM
- Structured logging (loguru)
- Resilient imports: will no-op if Redis or extensions are missing
"""

import os
import sys
import signal
import time
import json
from datetime import datetime, timezone

from loguru import logger

# --- Flask app ----------------------------------------------------------------
try:
    from app_pro import app
except Exception as e:
    print(f"[scheduler] FATAL: cannot import app_pro.app: {e}", file=sys.stderr)
    raise

# --- Extensions & Redis helpers ----------------------------------------------
def _get_redis():
    """Try to import a shared redis_client from extensions; if missing, build one."""
    try:
        from extensions import redis_client as shared_client  # type: ignore
        if shared_client:
            return shared_client
    except Exception:
        pass

    REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not REDIS_URL:
        return None
    try:
        import redis  # type: ignore
        return redis.from_url(REDIS_URL, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("Redis unavailable: {}", e)
        return None


redis_client = _get_redis()

# --- Queues & keys ------------------------------------------------------------
MAIL_QUEUE_KEY = os.getenv("MAIL_QUEUE_KEY", "queue:mail")
AI_QUEUE_KEY = os.getenv("AI_QUEUE_KEY", "queue:ai")
HEARTBEAT_KEY = os.getenv("SCHED_HEARTBEAT_KEY", "scheduler:heartbeat")
METRICS_KEY = os.getenv("SCHED_METRICS_KEY", "scheduler:metrics")

# --- Logging ------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, backtrace=False, diagnose=False, enqueue=True)

RUNNING = True


def _utc_now():
    return datetime.now(timezone.utc)


def heartbeat():
    if not redis_client:
        return
    try:
        redis_client.hset(
            HEARTBEAT_KEY,
            mapping={
                "ts": _utc_now().isoformat(),
                "pid": os.getpid(),
                "log_level": LOG_LEVEL,
                "ver": "1.0.0",
            },
        )
        redis_client.expire(HEARTBEAT_KEY, 180)  # 3m
    except Exception as e:
        logger.debug("Heartbeat failed: {}", e)


def incr_metric(name: str, by: int = 1):
    if not redis_client:
        return
    try:
        redis_client.hincrby(METRICS_KEY, name, by)
        redis_client.expire(METRICS_KEY, 86400)
    except Exception as e:
        logger.debug("Metric {} update failed: {}", name, e)


def enqueue(queue_key: str, payload: dict) -> bool:
    if not redis_client:
        logger.warning("enqueue() called but Redis not configured")
        return False
    try:
        redis_client.lpush(queue_key, json.dumps(payload))
        return True
    except Exception as e:
        logger.error("enqueue failed: {}", e)
        return False


# === Sample Jobs ==============================================================
def job_cache_warm_all():
    """Push cache warm tasks for worker to run."""
    logger.info("[job] cache_warm_all -> enqueue to AI queue (generic)")
    ok = enqueue(AI_QUEUE_KEY, {"type": "cache_warm_all"})
    incr_metric("jobs.cache_warm_all.enqueued", 1 if ok else 0)


def job_daily_email_digest():
    """Example daily digest email (worker will actually send it)."""
    sender = os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")
    to_email = os.getenv("DIGEST_TO_EMAIL", "").strip()
    if not to_email:
        logger.info("[job] daily_email_digest skipped: DIGEST_TO_EMAIL not set")
        return
    html = "<p>Your daily PittState-Connect digest is ready.</p>"
    ok = enqueue(MAIL_QUEUE_KEY, {"to": to_email, "subject": "Daily Digest", "html": html, "sender": sender})
    incr_metric("jobs.daily_digest.enqueued", 1 if ok else 0)


def job_scholarship_smartmatch_refresh():
    """Example: periodically refresh smart-match embeddings/training."""
    logger.info("[job] smart_match_train -> enqueue to AI")
    ok = enqueue(AI_QUEUE_KEY, {"type": "smart_match_train", "dataset": "internal"})
    incr_metric("jobs.smart_match_train.enqueued", 1 if ok else 0)


# === APScheduler bootstrap ====================================================
def _install_signal_handlers(scheduler):
    def _graceful(signum, frame):
        global RUNNING
        logger.warning("Signal {} received; scheduler shutting down…", signum)
        RUNNING = False
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

    signal.signal(signal.SIGINT, _graceful)
    signal.signal(signal.SIGTERM, _graceful)


def _add_jobs(sched):
    """
    Cron/intervals are env-configurable; sensible defaults provided.
    Use CRON_* envs for deployment-specific tuning without code changes.
    """
    # Cache warm: every 30 minutes
    cron_warm = os.getenv("CRON_CACHE_WARM", "*/30 * * * *")  # standard cron: m h dom mon dow
    sched.add_job(
        func=job_cache_warm_all,
        trigger="cron",
        id="cache_warm_all",
        minute=cron_warm.split()[0],
        hour=cron_warm.split()[1],
        day=cron_warm.split()[2],
        month=cron_warm.split()[3],
        day_of_week=cron_warm.split()[4],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Daily digest: default 07:00 UTC (adjust via CRON_DAILY_DIGEST)
    cron_digest = os.getenv("CRON_DAILY_DIGEST", "0 7 * * *")
    sched.add_job(
        func=job_daily_email_digest,
        trigger="cron",
        id="daily_email_digest",
        minute=cron_digest.split()[0],
        hour=cron_digest.split()[1],
        day=cron_digest.split()[2],
        month=cron_digest.split()[3],
        day_of_week=cron_digest.split()[4],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Smart-match refresh: hourly
    cron_sm = os.getenv("CRON_SMARTMATCH", "0 * * * *")
    sched.add_job(
        func=job_scholarship_smartmatch_refresh,
        trigger="cron",
        id="smartmatch_refresh",
        minute=cron_sm.split()[0],
        hour=cron_sm.split()[1],
        day=cron_sm.split()[2],
        month=cron_sm.split()[3],
        day_of_week=cron_sm.split()[4],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def main():
    from apscheduler.schedulers.background import BackgroundScheduler

    logger.info("Starting scheduler…")
    scheduler = BackgroundScheduler(timezone="UTC")
    _add_jobs(scheduler)
    _install_signal_handlers(scheduler)

    with app.app_context():
        scheduler.start()
        logger.info("APScheduler started with jobs: {}", [j.id for j in scheduler.get_jobs()])

        # Keep the process alive while RUNNING
        while RUNNING:
            heartbeat()
            time.sleep(2)

    logger.info("Scheduler stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
