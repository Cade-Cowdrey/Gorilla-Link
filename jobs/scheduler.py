# jobs/scheduler.py
from __future__ import annotations
from datetime import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from . import scheduler_state

def init_scheduler(app):
    if scheduler_state.get("scheduler"):
        return scheduler_state["scheduler"]

    sched = BackgroundScheduler(timezone="UTC")
    scheduler_state["scheduler"] = sched

    @sched.scheduled_job("interval", hours=1, id="collect_usage_metrics", max_instances=1, coalesce=True)
    def collect_usage_metrics():
        with app.app_context():
            try:
                from analytics.service import AnalyticsService
                db = app.extensions.get("sqlalchemy").db.session  # if you keep db global, adapt accordingly
                svc = AnalyticsService(db_session=db)

                users_series = [1180, 1192, 1201, 1215, 1228, 1276, 1287]
                anomalous, z = svc.detect_anomalies(users_series)
                kpis = svc.compute_core_kpis()
                anomalies = {"Active Users": z} if anomalous else {}

                output = os.path.join(app.static_folder, "analytics", "active_users.png")
                svc.generate_timeseries_chart("Active Users (7d)", users_series, output)

                logger.info({
                    "job": "collect_usage_metrics",
                    "kpis": [(k.label, k.value, k.delta) for k in kpis],
                    "anomalies": anomalies,
                    "chart": output
                })

                sock = app.extensions.get("socketio")
                if sock:
                    sock.emit("analytics:update", {
                        "kpis": [{"label": k.label, "value": k.value, "delta": k.delta, "unit": k.unit} for k in kpis],
                        "anomalies": anomalies,
                        "chart": "/static/analytics/active_users.png",
                        "ts": datetime.utcnow().isoformat()
                    }, namespace="/ws")
            except Exception as e:
                logger.warning(f"[Scheduler] Analytics job failed: {e}")

    @sched.scheduled_job("cron", day_of_week="sat", hour=9, minute=0, id="weekly_digest", coalesce=True)
    def weekly_digest():
        with app.app_context():
            try:
                from analytics.service import AnalyticsService
                from utils.mail import send_email
                from flask import render_template
                db = app.extensions.get("sqlalchemy").db.session
                svc = AnalyticsService(db_session=db)

                kpis = svc.compute_core_kpis()
                anomalies = {}
                body_html = svc.ai_weekly_brief(kpis, anomalies)
                html = render_template("emails/digest.html", body=body_html)

                recipients = app.config.get("DIGEST_RECIPIENTS", ["provost@pittstate.edu", "it@pittstate.edu"])
                send_email("PSU Impact Brief — Weekly", recipients, html=html)
                logger.info({"job": "weekly_digest", "sent_to": recipients})
            except Exception as e:
                logger.warning(f"[Scheduler] Weekly digest failed: {e}")

    sched.start()
    logger.info("Background scheduler started.")
    return sched
