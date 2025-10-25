# jobs/scheduler.py
from __future__ import annotations

import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

_scheduler: BackgroundScheduler | None = None

def init_scheduler(app: Flask) -> None:
    """Attach a background scheduler that runs WITHIN app context."""
    global _scheduler
    if _scheduler:  # already started (e.g., gunicorn worker reload)
        return

    _scheduler = BackgroundScheduler(timezone="UTC", daemon=True)

    @_scheduler.scheduled_job("interval", hours=1, id="collect_usage_metrics")
    def collect_usage_metrics():
        with app.app_context():
            try:
                # NOTE: keep it lightweight — just log and optionally touch Redis
                app.logger.info("[Scheduler] Collecting usage metrics (hourly).")
                # For demonstration, read latest 7d to ensure keys exist (warm caches)
                _ = app.analytics.get_timeseries(days=7)
            except Exception as exc:  # never crash the scheduler
                app.logger.warning("[Scheduler] Analytics job failed: %s", exc)

    # Optional startup warmup (fires once ~15s after boot)
    @_scheduler.scheduled_job("date", run_date=None, id="startup_warmup")
    def warmup():
        with app.app_context():
            try:
                app.logger.info("[Scheduler] Warmup (preloading analytics).")
                _ = app.analytics.get_summary()
            except Exception as exc:
                app.logger.warning("[Scheduler] Warmup failed: %s", exc)

    _scheduler.start()
    app.logger.info("Background scheduler started.")
