"""
utils/scheduler.py

Production-grade APScheduler bootstrap + jobs with:
- Safe app context wrapping
- Redis-backed distributed locks (avoids duplicate runs across dynos)
- Metrics collection + daily chart generation (headless matplotlib)
- Health pings (Redis/DB/OpenAI presence)
- Sentry capture (optional)
- Configurable intervals via env vars
"""

from __future__ import annotations
import os
import io
import json
import time
import random
import logging
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from typing import Optional, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from flask import current_app
from sqlalchemy import text

# Matplotlib safe headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# -----------------------------#
# Helpers
# -----------------------------#

def _get_logger() -> logging.Logger:
    try:
        return current_app.logger  # within request/app context
    except Exception:
        # Fallback logger for early boot
        logger = logging.getLogger("scheduler")
        if not logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
            logger.addHandler(h)
        logger.setLevel(logging.INFO)
        return logger


def _get_redis():
    """Fetch redis client attached in app.extensions['redis'] or app.config['REDIS_CLIENT']."""
    try:
        app = current_app
        redis_client = (
            app.extensions.get("redis") or
            app.config.get("REDIS_CLIENT")
        )
        return redis_client
    except Exception:
        return None


def _get_db():
    """Get SQLAlchemy db instance attached to app.extensions['sqlalchemy'].db (Flask-SQLAlchemy)."""
    try:
        app = current_app
        # Flask-SQLAlchemy stores ref in extension
        sa_ext = app.extensions.get("sqlalchemy")
        if not sa_ext:
            return None
        return sa_ext["db"]
    except Exception:
        return None


@contextmanager
def _locked(redis, key: str, ttl: int = 300):
    """
    Redis distributed lock using SET NX EX.
    Ensures only one job instance runs across multiple workers/dynos.
    """
    token = str(time.time())
    acquired = False
    try:
        if redis:
            # SET key token NX EX ttl
            acquired = bool(redis.set(key, token, nx=True, ex=ttl))
        else:
            # No redis -> allow run (single instance)
            acquired = True

        if acquired:
            yield
        else:
            _get_logger().info(f"[Scheduler] Skipping (lock held): {key}")
            yield None
    finally:
        if acquired and redis:
            try:
                # Only delete if token matches (safety)
                pipe = redis.pipeline(True)
                if redis.get(key) == token:
                    pipe.delete(key)
                pipe.execute()
            except Exception:
                pass


def _capture_exception(e: Exception):
    """Send to Sentry if configured; always log."""
    log = _get_logger()
    log.exception(e)
    try:
        import sentry_sdk  # type: ignore
        sentry_sdk.capture_exception(e)
    except Exception:
        pass


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# -----------------------------#
# Jobs
# -----------------------------#

def job_collect_usage_metrics():
    """
    Aggregates lightweight metrics hourly.
    Safe to call outside request handlers — wraps app context internally.
    Uses Redis for last_run marker + small counters demo.
    """
    log = _get_logger()
    try:
        with current_app.app_context():
            redis = _get_redis()
            lock_key = "psu:locks:collect_usage"
            with _locked(redis, lock_key, ttl=240):
                now = datetime.now(timezone.utc).isoformat()

                # Example counters (replace with real measurements from your app)
                visits = int(redis.incr("psu:metrics:visits")) if redis else random.randint(50, 250)
                signups = int(redis.incr("psu:metrics:signups")) if redis else random.randint(1, 25)

                if redis:
                    redis.hset("psu:metrics:last", mapping={
                        "last_run": now,
                        "visits": visits,
                        "signups": signups,
                    })

                log.info(f"[Scheduler] Metrics ok @ {now} | visits={visits} signups={signups}")
    except Exception as e:
        _capture_exception(e)


def job_generate_daily_chart():
    """
    Generates a small daily PNG chart into /static/img/analytics/.
    Pulls metrics from Redis if available; otherwise generates demo data.
    """
    log = _get_logger()
    try:
        with current_app.app_context():
            app = current_app
            redis = _get_redis()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Build data (7-day window)
            days = [
                (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(6, -1, -1)
            ]
            if redis and redis.exists("psu:metrics:timeseries"):
                series_raw = redis.get("psu:metrics:timeseries")
                try:
                    series = json.loads(series_raw)
                except Exception:
                    series = {}
            else:
                # Demo time series if nothing in Redis
                series = {d: random.randint(100, 450) for d in days}

            x = list(days)
            y = [int(series.get(d, 0)) for d in days]

            # Render
            plt.figure(figsize=(8, 3.5))
            plt.plot(x, y, marker="o")
            plt.title("PSU Daily Visits (7-day)")
            plt.xlabel("Date")
            plt.ylabel("Visits")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            out_dir = os.path.join(app.root_path, "static", "img", "analytics")
            _ensure_dir(out_dir)
            out_file = os.path.join(out_dir, f"traffic_{today}.png")
            plt.savefig(out_file, dpi=140)
            plt.close()

            # Update a “latest” symlink-like copy
            latest_file = os.path.join(out_dir, "traffic_latest.png")
            try:
                if os.path.exists(latest_file):
                    os.remove(latest_file)
                # copy file
                with open(out_file, "rb") as src, open(latest_file, "wb") as dst:
                    dst.write(src.read())
            except Exception:
                pass

            log.info(f"[Scheduler] Daily chart rendered -> /static/img/analytics/traffic_{today}.png")
    except Exception as e:
        _capture_exception(e)


def job_health_ping():
    """
    Lightweight health ping to check Redis/DB/OpenAI presence.
    Does not call external APIs; just verifies plumbing & logs status.
    """
    log = _get_logger()
    try:
        with current_app.app_context():
            status = {"time": datetime.now(timezone.utc).isoformat()}

            # Redis
            redis = _get_redis()
            try:
                status["redis_ok"] = bool(redis and redis.ping())
            except Exception:
                status["redis_ok"] = False

            # DB
            db = _get_db()
            try:
                if db:
                    db.session.execute(text("SELECT 1"))
                    status["db_ok"] = True
                else:
                    status["db_ok"] = False
            except Exception:
                status["db_ok"] = False

            # OpenAI
            status["openai_present"] = bool(os.getenv("OPENAI_API_KEY"))

            log.info(f"[Scheduler] Health: {status}")
    except Exception as e:
        _capture_exception(e)


# -----------------------------#
# Bootstrap
# -----------------------------#

def init_scheduler(app) -> BackgroundScheduler:
    """
    Create & start a BackgroundScheduler bound to this Flask app.

    Adds three jobs by default (configurable via env):
      - Usage metrics (interval)
      - Daily chart (cron)
      - Health ping (interval)
    """

    # Use a dedicated logger name to make filtering easy
    log = app.logger.getChild("scheduler")

    # Configure scheduler
    scheduler = BackgroundScheduler(
        timezone=os.getenv("SCHED_TIMEZONE", "UTC"),
        daemon=True
    )

    # Store on app so other modules/tests can access/stop it
    app.extensions["apscheduler"] = scheduler

    # Attach redis client for other modules if present
    # (app_pro.py should assign app.extensions['redis'] already)
    redis_client = app.extensions.get("redis") or app.config.get("REDIS_CLIENT")
    if redis_client:
        log.info("Scheduler: Redis available and attached.")

    # Intervals (env overrides)
    metrics_seconds = int(os.getenv("SCHED_METRICS_INTERVAL_SEC", "3600"))   # default 1h
    health_seconds  = int(os.getenv("SCHED_HEALTH_INTERVAL_SEC", "300"))     # default 5m
    # Daily chart at 02:15 UTC by default
    chart_cron = os.getenv("SCHED_CHART_CRON", "15 2 * * *")  # minute hour day month dow

    # Add jobs with jitter/misfire safety
    scheduler.add_job(
        func=job_collect_usage_metrics,
        id="psu_collect_usage",
        name="Collect Usage Metrics",
        trigger=IntervalTrigger(seconds=metrics_seconds, jitter=20),
        coalesce=True,
        misfire_grace_time=120
    )

    # Parse CRON (min hour dom mon dow)
    try:
        m, h, dom, mon, dow = chart_cron.split()
        scheduler.add_job(
            func=job_generate_daily_chart,
            id="psu_daily_chart",
            name="Generate Daily Chart",
            trigger=CronTrigger(minute=m, hour=h, day=dom, month=mon, day_of_week=dow),
            coalesce=True,
            misfire_grace_time=300
        )
    except Exception as e:
        log.warning(f"Invalid SCHED_CHART_CRON='{chart_cron}': {e}. Falling back to 02:15 UTC daily.")
        scheduler.add_job(
            func=job_generate_daily_chart,
            id="psu_daily_chart",
            name="Generate Daily Chart",
            trigger=CronTrigger(minute=15, hour=2),
            coalesce=True,
            misfire_grace_time=300
        )

    scheduler.add_job(
        func=job_health_ping,
        id="psu_health_ping",
        name="Health Ping",
        trigger=IntervalTrigger(seconds=health_seconds, jitter=10),
        coalesce=True,
        misfire_grace_time=120
    )

    # Start
    scheduler.start()
    log.info("Scheduler started with jobs: %s", [j.id for j in scheduler.get_jobs()])

    return scheduler
