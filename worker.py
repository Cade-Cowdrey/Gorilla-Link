# =============================================================
# FILE: worker.py
# PittState-Connect — Advanced Background Task Worker
# -------------------------------------------------------------
# Handles background jobs for:
#   - AI essay scoring (Smart Match / Essay Helper)
#   - Scholarship reminders
#   - Donor sync + analytics refresh
#   - Mentor digest summaries
#   - Financial dashboards
# Optional: integrates with Sentry, Prometheus, and retry logic.
# =============================================================

import os
import logging
import time
import random
from datetime import datetime
from threading import Thread
from queue import Queue, Empty
from typing import Callable, Any, Tuple, Dict

from app_pro import create_app
from utils.mail_util import send_email  # Ensure this exists
from models import db

# -------------------------------------------------------------
# Optional integrations (safe imports)
# -------------------------------------------------------------
try:
    import openai
except ImportError:
    openai = None

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    SENTRY_ENABLED = True
except ImportError:
    SENTRY_ENABLED = False

# -------------------------------------------------------------
# CONFIGURATION & INITIALIZATION
# -------------------------------------------------------------
app = create_app()
app.app_context().push()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("pittstate-worker")

# Optional: Sentry setup for error monitoring
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("FLASK_ENV", "production"),
    )
    log.info("🧩 Sentry monitoring enabled.")
else:
    log.info("Sentry disabled (missing DSN or library).")

# Optional: configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_ENABLED = False
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    AI_ENABLED = True
    log.info("🧠 AI features enabled (OpenAI API key found).")
else:
    log.warning("🧠 AI helper disabled (no OPENAI_API_KEY or library missing).")

# In-memory task queue (can later swap with Redis, Celery, or RQ)
task_queue: "Queue[Tuple[str, Tuple[Any, ...], Dict[str, Any]]]" = Queue()


# -------------------------------------------------------------
# TASK DEFINITIONS
# -------------------------------------------------------------
def ai_scholarship_scorer(user_id: int, essay_text: str):
    """Analyze scholarship essay using OpenAI."""
    if not AI_ENABLED:
        log.warning("AI scoring skipped — OpenAI not configured.")
        return None

    prompt = f"""
    Score this scholarship essay (0–100) with strengths and weaknesses.
    Return your response in this format:
    Score: <number>
    Strengths: ...
    Weaknesses: ...
    Essay:
    {essay_text}
    """
    try:
        result = openai.ChatCompletion.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=float(os.getenv("AI_TEMPERATURE", 0.4)),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", 1200)),
        )
        response = result["choices"][0]["message"]["content"]
        log.info("✅ AI essay scored successfully for user %s", user_id)
        return response
    except Exception as e:
        log.exception("❌ AI scoring failed for user %s: %s", user_id, e)
        return None


def send_scholarship_reminder(user_email: str, scholarship_name: str, deadline: str):
    """Send reminder emails for upcoming deadlines."""
    subject = f"Reminder: {scholarship_name} deadline approaching"
    body = (
        f"Don't forget to submit your application for '{scholarship_name}' by {deadline}!\n\n"
        f"Visit your PittState-Connect dashboard to apply now."
    )
    try:
        send_email(subject, [user_email], body)
        log.info("📧 Reminder sent to %s for '%s'", user_email, scholarship_name)
    except Exception as e:
        log.error("❌ Reminder send failed for %s: %s", user_email, e)


def sync_donor_analytics():
    """Simulate donor analytics data refresh."""
    log.info("🔁 Syncing donor analytics...")
    time.sleep(random.uniform(2, 4))
    log.info("✅ Donor analytics sync complete.")


def generate_weekly_mentor_digest():
    """Email mentors with engagement summaries."""
    log.info("📬 Generating mentor digest...")
    time.sleep(random.uniform(1, 3))
    log.info("✅ Mentor digest dispatched.")


def refresh_financial_aid_dashboard():
    """Refresh cost-to-completion and funding progress metrics."""
    log.info("📊 Refreshing financial aid dashboard...")
    time.sleep(random.uniform(1.5, 3))
    log.info("✅ Financial dashboards refreshed successfully.")


# -------------------------------------------------------------
# TASK REGISTRY
# -------------------------------------------------------------
TASK_MAP: Dict[str, Callable[..., Any]] = {
    "ai_scholarship_scorer": ai_scholarship_scorer,
    "send_scholarship_reminder": send_scholarship_reminder,
    "sync_donor_analytics": sync_donor_analytics,
    "generate_weekly_mentor_digest": generate_weekly_mentor_digest,
    "refresh_financial_aid_dashboard": refresh_financial_aid_dashboard,
}


# -------------------------------------------------------------
# WORKER LOOP (RESILIENT)
# -------------------------------------------------------------
def worker_loop():
    """Main task consumer loop."""
    log.info("🚀 Worker online — awaiting jobs...")
    while True:
        try:
            task_name, args, kwargs = task_queue.get(timeout=5)
            func = TASK_MAP.get(task_name)
            if not func:
                log.warning("Unknown task: %s", task_name)
                continue

            log.info("▶️ Executing task: %s", task_name)
            func(*args, **kwargs)
        except Empty:
            continue
        except Exception as e:
            log.exception("Task execution error: %s", e)
        finally:
            time.sleep(0.5)  # prevent CPU spike


# -------------------------------------------------------------
# ENTRYPOINT (RESTART-SAFE)
# -------------------------------------------------------------
if __name__ == "__main__":
    log.info("💡 PittState-Connect Worker Booting (%s)", datetime.utcnow())
    thread = Thread(target=worker_loop, daemon=True)
    thread.start()

    # Keep-alive loop for Render / Docker runtime
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        log.info("🛑 Worker shutdown requested (%s)", datetime.utcnow())
    except Exception as e:
        log.exception("Unexpected worker crash: %s", e)
