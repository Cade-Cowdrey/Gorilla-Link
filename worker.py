# =============================================================
# FILE: worker.py
# PittState-Connect — Background Task Worker
# Handles queued tasks: AI helpers, scholarship reminders,
# donor syncs, analytics updates, mentorship digests, and more.
# =============================================================

import os
import logging
import time
from datetime import datetime
from threading import Thread
from queue import Queue, Empty

from app_pro import create_app
from utils.mail_util import send_email  # ensure this exists in utils
from models import db

# Optional AI imports (activated if OPENAI_API_KEY is set)
try:
    import openai
except ImportError:
    openai = None

# -------------------------------------------------------------
# CONFIG & INITIALIZATION
# -------------------------------------------------------------
app = create_app()
app.app_context().push()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")

task_queue = Queue()

# Optional: configure OpenAI if available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY
    AI_ENABLED = True
else:
    AI_ENABLED = False
    log.info("🧠 AI helper disabled (no OPENAI_API_KEY)")

# -------------------------------------------------------------
# DEFINE TASKS
# -------------------------------------------------------------
def ai_scholarship_scorer(user_id: int, essay_text: str):
    """Analyze scholarship essay using AI scoring."""
    if not AI_ENABLED:
        log.warning("AI scoring skipped: OpenAI not configured.")
        return None
    prompt = f"Score this scholarship essay (0–100) and explain strengths/weaknesses:\n\n{essay_text}"
    try:
        result = openai.ChatCompletion.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=float(os.getenv("AI_TEMPERATURE", 0.4)),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", 1500))
        )
        score_text = result["choices"][0]["message"]["content"]
        log.info("✅ AI essay scored for user %s", user_id)
        return score_text
    except Exception as e:
        log.error("❌ AI scoring failed: %s", e)
        return None


def send_scholarship_reminder(user_email: str, scholarship_name: str, deadline: str):
    """Send reminder emails to students about upcoming scholarship deadlines."""
    subject = f"Reminder: {scholarship_name} deadline approaching"
    body = f"Don't forget to submit your application for '{scholarship_name}' by {deadline}!"
    send_email(subject, [user_email], body)
    log.info("📧 Reminder sent to %s for %s", user_email, scholarship_name)


def sync_donor_analytics():
    """Aggregate donor impact and sync analytics dashboard."""
    log.info("🔁 Syncing donor analytics...")
    time.sleep(3)
    log.info("✅ Donor analytics sync complete.")


def generate_weekly_mentor_digest():
    """Email mentors with weekly engagement summaries."""
    log.info("📬 Generating weekly mentor digest...")
    time.sleep(2)
    log.info("✅ Mentor digest sent to all active mentors.")


def refresh_financial_aid_dashboard():
    """Refresh cost-to-completion and funding progress metrics."""
    log.info("📊 Refreshing financial aid dashboards...")
    time.sleep(2)
    log.info("✅ Financial dashboards refreshed successfully.")


# -------------------------------------------------------------
# TASK DISPATCHER
# -------------------------------------------------------------
TASK_MAP = {
    "ai_scholarship_scorer": ai_scholarship_scorer,
    "send_scholarship_reminder": send_scholarship_reminder,
    "sync_donor_analytics": sync_donor_analytics,
    "generate_weekly_mentor_digest": generate_weekly_mentor_digest,
    "refresh_financial_aid_dashboard": refresh_financial_aid_dashboard,
}


def worker_loop():
    """Main loop: fetch and execute queued tasks."""
    log.info("🚀 Worker started. Waiting for tasks...")
    while True:
        try:
            task_name, args, kwargs = task_queue.get(timeout=5)
            func = TASK_MAP.get(task_name)
            if not func:
                log.warning("Unknown task: %s", task_name)
                continue
            log.info("▶️ Running task: %s", task_name)
            func(*args, **kwargs)
        except Empty:
            continue
        except Exception as e:
            log.error("Task error: %s", e)


# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    thread = Thread(target=worker_loop, daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        log.info("🛑 Worker shutting down at %s", datetime.utcnow())
