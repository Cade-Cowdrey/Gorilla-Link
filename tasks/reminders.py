# ===============================================================
#  PittState-Connect — Scheduled Jobs (Final, Advanced)
#  File: tasks/reminders.py
#  ---------------------------------------------------------------
#  Exposes functions used by app_pro.py's scheduler:
#     • run_daily_digest_job(app)
#     • run_deadline_reminders_job(app)
#  Optional enhancements:
#     • weekly_analytics_rollup(app)
#     • cache_prime_job(app)
#     • stale_session_cleanup(app)
#  Features:
#     • App-context aware jobs with robust logging
#     • Redis cache support (fallback to in-memory)
#     • Mail digests & deadline alerts via Flask-Mail
#     • Activity webhooks (Slack/Discord/Teams/etc.)
#     • Exponential backoff for transient failures
# ===============================================================

from __future__ import annotations

import os
import json
import time
import random
import logging
import smtplib
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from flask import current_app
from flask_mail import Message

# Optional Redis for caching
try:
    import redis  # type: ignore
except Exception:
    redis = None

# ---------------------------------------------------------------
#  Config & Utilities
# ---------------------------------------------------------------
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., Slack/Discord/Teams
REDIS_URL = os.getenv("REDIS_URL")
MAIL_FROM = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.edu")

# Connect to Redis if configured
_redis = None
if REDIS_URL and redis:
    try:
        _redis = redis.from_url(REDIS_URL)
    except Exception:
        _redis = None

# In-memory cache fallback (very light)
_mem_cache: Dict[str, Dict[str, Any]] = {}


def _cache_get(key: str) -> Optional[dict]:
    if _redis:
        raw = _redis.get(key)
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None
    return _mem_cache.get(key)


def _cache_set(key: str, value: dict, ttl_sec: int = 300) -> None:
    if _redis:
        _redis.setex(key, ttl_sec, json.dumps(value))
    else:
        _mem_cache[key] = value


def _cache_del(key: str) -> None:
    if _redis:
        _redis.delete(key)
    else:
        _mem_cache.pop(key, None)


def _emit_activity(event_type: str, payload: dict, logger: logging.Logger) -> None:
    """Send a structured event to an external webhook (optional)."""
    if not WEBHOOK_URL:
        logger.info(f"[Webhook disabled] {event_type}: {payload}")
        return

    try:
        import urllib.request  # defer import
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps({"type": event_type, "data": payload}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as _:
            pass
        logger.info(f"[Webhook] emitted {event_type}")
    except Exception as e:
        logger.warning(f"[Webhook] failed for {event_type}: {e}")


def _backoff(delays=(0.4, 1.0, 2.0, 4.0)):
    """Simple backoff generator for retry loops."""
    for d in delays:
        yield d + random.uniform(0, 0.2)


# ---------------------------------------------------------------
#  Email Helpers
# ---------------------------------------------------------------
def _send_mail(app, subject: str, recipients: list[str], html_body: str, logger: logging.Logger) -> bool:
    """Send a single email with retries; returns True on success."""
    if not recipients:
        logger.info("[Mail] No recipients, skipping send.")
        return True

    try:
        from app_pro import mail  # import the Flask-Mail instance from app context
    except Exception:
        logger.error("[Mail] Flask-Mail not available.")
        return False

    msg = Message(subject=subject, recipients=recipients, sender=MAIL_FROM)
    msg.html = html_body

    for delay in _backoff():
        try:
            with app.app_context():
                mail.send(msg)
            logger.info(f"[Mail] Sent '{subject}' to {len(recipients)} recipient(s).")
            return True
        except smtplib.SMTPException as e:
            logger.warning(f"[Mail] SMTPException, retrying in {delay:.1f}s: {e}")
            time.sleep(delay)
        except Exception as e:
            logger.warning(f"[Mail] Error, retrying in {delay:.1f}s: {e}")
            time.sleep(delay)

    logger.error(f"[Mail] Failed to send '{subject}' after retries.")
    return False


# ---------------------------------------------------------------
#  Data Fetch Stubs (Replace with DB queries)
# ---------------------------------------------------------------
def _get_students_with_upcoming_deadlines(app) -> list[dict]:
    """
    TODO: Replace with real database queries.
    Return a list of student dicts, each with: email, name, deadlines:[{title, due_date, url}]
    """
    # Example mock data
    now = datetime.utcnow().date()
    return [
        {
            "email": "student1@psu.edu",
            "name": "Alex Johnson",
            "deadlines": [
                {"title": "STEM Excellence Grant", "due_date": (now + timedelta(days=2)).isoformat(), "url": "/scholarships/123"},
                {"title": "Leadership Award", "due_date": (now + timedelta(days=5)).isoformat(), "url": "/scholarships/456"},
            ],
        },
        {
            "email": "student2@psu.edu",
            "name": "Taylor Kim",
            "deadlines": [
                {"title": "Business Innovation Fund", "due_date": (now + timedelta(days=1)).isoformat(), "url": "/scholarships/789"},
            ],
        },
    ]


def _get_daily_digest_targets(app) -> list[dict]:
    """
    TODO: Replace with real database queries.
    Return targets for daily digests: admin/faculty/staff or opt-in students.
    Each item contains: email, name, role, preferences, scope (e.g., 'admin','faculty','student')
    """
    return [
        {"email": "dean@psu.edu", "name": "Dean of Students", "role": "admin", "scope": "admin"},
        {"email": "advisor@psu.edu", "name": "Advising Office", "role": "faculty", "scope": "faculty"},
    ]


def _render_deadline_html(student: dict, items: list[dict]) -> str:
    lines = [
        f"<p>Hello {student.get('name','Gorilla')} 🦍,</p>",
        "<p>Here are your upcoming scholarship deadlines:</p>",
        "<ul>",
    ]
    for it in items:
        due = datetime.fromisoformat(it["due_date"]).strftime("%b %d")
        lines.append(f'<li><strong>{it["title"]}</strong> — due <em>{due}</em> · <a href="{it["url"]}">Open →</a></li>')
    lines.append("</ul>")
    lines.append("<p>Good luck! — PittState-Connect</p>")
    return "\n".join(lines)


def _render_digest_html(scope: str, metrics: dict) -> str:
    return f"""
      <h2>Daily Digest — {scope.title()}</h2>
      <p>Here are today’s platform highlights:</p>
      <ul>
        <li>Total Users: <strong>{metrics.get('users_total','–')}</strong></li>
        <li>Active Sessions: <strong>{metrics.get('active_sessions','–')}</strong></li>
        <li>Open Scholarships: <strong>{metrics.get('open_scholarships','–')}</strong></li>
        <li>Upcoming Events: <strong>{metrics.get('events_upcoming','–')}</strong></li>
        <li>Jobs Posted: <strong>{metrics.get('jobs_posted','–')}</strong></li>
        <li>Avg Match Score: <strong>{metrics.get('avg_match_score','–')}%</strong></li>
      </ul>
      <p>View full dashboard: <a href="/analytics">Analytics →</a></p>
    """


# ---------------------------------------------------------------
#  Core Job: Deadline Reminders
# ---------------------------------------------------------------
def run_deadline_reminders_job(app) -> None:
    """
    Sends individualized scholarship deadline reminders.
    - Looks up upcoming deadlines per student
    - Sends email (HTML)
    - Emits activity webhook events
    """
    logger = app.logger
    started = time.time()
    try:
        with app.app_context():
            students = _get_students_with_upcoming_deadlines(app)
            sent_count = 0
            for s in students:
                items = s.get("deadlines", [])
                if not items:
                    continue
                html = _render_deadline_html(s, items)
                ok = _send_mail(app, subject="Upcoming Scholarship Deadlines", recipients=[s["email"]], html_body=html, logger=logger)
                if ok:
                    sent_count += 1

            _emit_activity(
                "job.deadline_reminders",
                {"sent": sent_count, "students": len(students), "duration_s": round(time.time() - started, 2)},
                logger,
            )
            logger.info(f"[Reminders] Completed: sent={sent_count} students={len(students)}")
    except Exception as e:
        logger.error(f"[Reminders] Error: {e}\n{traceback.format_exc()}")
        _emit_activity("job.deadline_reminders.error", {"error": str(e)}, logger)


# ---------------------------------------------------------------
#  Core Job: Daily Digest
# ---------------------------------------------------------------
def run_daily_digest_job(app) -> None:
    """
    Sends a daily digest to configured recipients (admins/faculty/staff or opted-in students).
    - Pulls current analytics summary (cached)
    - Sends a tailored digest per scope
    - Emits activity webhook events
    """
    logger = app.logger
    started = time.time()
    try:
        with app.app_context():
            # Pull analytics summary from cache (or compute default)
            metrics = _cache_get("analytics:summary") or {
                "users_total": 4528,
                "alumni": 1679,
                "active_sessions": 118,
                "open_scholarships": 41,
                "events_upcoming": 14,
                "jobs_posted": 89,
                "avg_match_score": 88,
            }

            targets = _get_daily_digest_targets(app)
            sent = 0
            for t in targets:
                scope = t.get("scope", "admin")
                html = _render_digest_html(scope, metrics)
                ok = _send_mail(app, subject="PittState Daily Digest", recipients=[t["email"]], html_body=html, logger=logger)
                if ok:
                    sent += 1

            _emit_activity(
                "job.daily_digest",
                {"sent": sent, "targets": len(targets), "duration_s": round(time.time() - started, 2)},
                logger,
            )
            logger.info(f"[Digest] Completed: sent={sent} targets={len(targets)}")
    except Exception as e:
        logger.error(f"[Digest] Error: {e}\n{traceback.format_exc()}")
        _emit_activity("job.daily_digest.error", {"error": str(e)}, logger)


# ---------------------------------------------------------------
#  Enhancement: Weekly Analytics Rollup
# ---------------------------------------------------------------
def weekly_analytics_rollup(app) -> None:
    """
    Snapshots current analytics into 'analytics:summary:prev' for
    week-over-week AI comparisons and trend diffs.
    """
    logger = app.logger
    try:
        with app.app_context():
            current = _cache_get("analytics:summary")
            if not current:
                # Try priming from API if needed (optional: local import to avoid circularity)
                current = {
                    "users_total": 4528, "alumni": 1679, "active_sessions": 118,
                    "open_scholarships": 41, "events_upcoming": 14, "jobs_posted": 89,
                    "avg_match_score": 88
                }
            _cache_set("analytics:summary:prev", current, ttl_sec=7 * 24 * 3600)
            _emit_activity("job.weekly_rollup", {"snapshot": True}, logger)
            logger.info("[Weekly Rollup] Previous snapshot updated.")
    except Exception as e:
        logger.error(f"[Weekly Rollup] Error: {e}\n{traceback.format_exc()}")
        _emit_activity("job.weekly_rollup.error", {"error": str(e)}, logger)


# ---------------------------------------------------------------
#  Enhancement: Cache Prime (pre-warm dashboard data)
# ---------------------------------------------------------------
def cache_prime_job(app) -> None:
    """
    Pre-warm frequently used cache keys for snappy dashboards.
    """
    logger = app.logger
    try:
        with app.app_context():
            summary = {
                "users_total": 4528,
                "alumni": 1679,
                "active_sessions": 118,
                "open_scholarships": 41,
                "events_upcoming": 14,
                "jobs_posted": 89,
                "avg_match_score": 88,
            }
            trends = {
                "labels": [(datetime.utcnow().date() - timedelta(days=7 * i)).strftime("%b %d") for i in range(6, -1, -1)],
                "users": [3800, 3925, 4010, 4150, 4275, 4410, 4528],
                "sessions": [92, 101, 95, 108, 113, 119, 118],
                "jobs": [70, 72, 74, 78, 80, 85, 89],
                "events": [10, 11, 10, 12, 12, 13, 14],
            }
            _cache_set("analytics:summary", summary, ttl_sec=300)
            _cache_set("analytics:trends", trends, ttl_sec=600)
            _emit_activity("job.cache_prime", {"primed": ["analytics:summary", "analytics:trends"]}, logger)
            logger.info("[Cache Prime] analytics summary & trends set.")
    except Exception as e:
        logger.error(f"[Cache Prime] Error: {e}\n{traceback.format_exc()}")
        _emit_activity("job.cache_prime.error", {"error": str(e)}, logger)


# ---------------------------------------------------------------
#  Enhancement: Stale Session Cleanup (example maintenance)
# ---------------------------------------------------------------
def stale_session_cleanup(app) -> None:
    """
    Demonstration maintenance task:
    - Cleans up expired server-side sessions if using Flask-Session filesystem.
    - Replace with actual session store cleanup as needed.
    """
    logger = app.logger
    try:
        with app.app_context():
            # If using filesystem sessions, you can safely remove stale files here.
            # Keep this as a placeholder to avoid accidental deletions in production.
            pruned = 0
            _emit_activity("job.session_cleanup", {"pruned": pruned}, logger)
            logger.info("[Session Cleanup] Completed, files pruned=%s", pruned)
    except Exception as e:
        logger.error(f"[Session Cleanup] Error: {e}\n{traceback.format_exc()}")
        _emit_activity("job.session_cleanup.error", {"error": str(e)}, logger)


# ---------------------------------------------------------------
#  Manual Execution (Optional)
#  Run these for local testing:
#     python -m tasks.reminders daily
#     python -m tasks.reminders deadlines
#     python -m tasks.reminders rollup
#     python -m tasks.reminders prime
#     python -m tasks.reminders cleanup
# ---------------------------------------------------------------
if __name__ == "__main__":
    # Minimal local runner — builds a bare Flask app to satisfy context.
    from flask import Flask
    from flask_mail import Mail

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev",
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=MAIL_FROM,
    )
    Mail(app)

    import sys
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    with app.app_context():
        if cmd == "daily":
            run_daily_digest_job(app)
        elif cmd == "deadlines":
            run_deadline_reminders_job(app)
        elif cmd == "rollup":
            weekly_analytics_rollup(app)
        elif cmd == "prime":
            cache_prime_job(app)
        elif cmd == "cleanup":
            stale_session_cleanup(app)
        else:
            print("Usage: python -m tasks.reminders [daily|deadlines|rollup|prime|cleanup]")
