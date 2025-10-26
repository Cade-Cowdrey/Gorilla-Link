#!/usr/bin/env python3
"""
PittState-Connect Background Worker
- Mail queue processor (Redis)
- OpenAI/AI task runner (Redis)
- Cache warmers (departments, scholarships, careers)
- Heartbeat + metrics (Redis)
- Graceful shutdown on SIGINT/SIGTERM
- Structured logging via loguru, colorized in dev
"""

import os
import sys
import time
import json
import signal
import argparse
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

from loguru import logger

# --- Flask app & extensions ---------------------------------------------------
try:
    # Prefer app factory if you have one; fallback to `app` object.
    # from app_pro import create_app
    # app = create_app()
    from app_pro import app  # existing pattern in your project
except Exception as e:
    print(f"[worker] FATAL: could not import app_pro.app: {e}", file=sys.stderr)
    raise

# Extensions live behind your central `extensions.py`
try:
    from extensions import db, cache, mail, scheduler  # login_manager not needed here
except Exception as e:
    logger.warning("extensions import failed (db/cache/mail/scheduler may be None): {}", e)
    db = cache = mail = scheduler = None  # continue with fallbacks

# --- Third-party clients ------------------------------------------------------
# Redis (for queues, heartbeats, metrics)
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
redis_client = None
if REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True, retry_on_timeout=True)
    except Exception as e:
        logger.error("Failed to initialize Redis client: {}", e)

# SendGrid (primary) + Flask-Mail (fallback)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
sendgrid_client = None
if SENDGRID_API_KEY:
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail as SGMail, From, To, Subject, HtmlContent
        sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        logger.error("Failed to initialize SendGrid client: {}", e)
        sendgrid_client = None

# OpenAI (optional AI helper)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
openai = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.error("Failed to initialize OpenAI client: {}", e)
        openai = None

# --- Queues & Keys ------------------------------------------------------------
MAIL_QUEUE_KEY = os.getenv("MAIL_QUEUE_KEY", "queue:mail")
AI_QUEUE_KEY = os.getenv("AI_QUEUE_KEY", "queue:ai")
HEARTBEAT_KEY = os.getenv("WORKER_HEARTBEAT_KEY", "worker:heartbeat")
METRICS_KEY = os.getenv("WORKER_METRICS_KEY", "worker:metrics")

# --- Logging config -----------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, backtrace=False, diagnose=False, enqueue=True)

# --- Control flags ------------------------------------------------------------
RUNNING = True


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).lower() in {"1", "true", "yes", "on"}


def _in_app_context():
    """Ensure we always have an application context around work units."""
    if app is None:
        raise RuntimeError("Flask app not available")
    return app.app_context()


@contextmanager
def app_context():
    with _in_app_context():
        yield


# --- Heartbeat & Metrics ------------------------------------------------------
def heartbeat():
    if not redis_client:
        return
    try:
        redis_client.hset(
            HEARTBEAT_KEY,
            mapping={
                "ts": _utc_now().isoformat(),
                "pid": os.getpid(),
                "queues": json.dumps({"mail": MAIL_QUEUE_KEY, "ai": AI_QUEUE_KEY}),
                "log_level": LOG_LEVEL,
                "ver": "1.0.0",
            },
        )
        redis_client.expire(HEARTBEAT_KEY, 180)  # 3 minutes TTL
    except Exception as e:
        logger.warning("Heartbeat failed: {}", e)


def incr_metric(name: str, by: int = 1):
    if not redis_client:
        return
    try:
        redis_client.hincrby(METRICS_KEY, name, by)
        redis_client.expire(METRICS_KEY, 86400)  # 1 day
    except Exception as e:
        logger.debug("Metric {} update failed: {}", name, e)


# --- Email sending ------------------------------------------------------------
def send_email_via_sendgrid(to_email: str, subject: str, html: str, sender: str) -> bool:
    if not sendgrid_client:
        return False
    try:
        msg = SGMail(from_email=From(sender), to_emails=To(to_email),
                     subject=Subject(subject), html_content=HtmlContent(html))
        resp = sendgrid_client.send(msg)
        ok = 200 <= int(resp.status_code) < 300
        if not ok:
            logger.warning("SendGrid non-2xx: {}", resp.status_code)
        return ok
    except Exception as e:
        logger.error("SendGrid send failed: {}", e)
        return False


def send_email_via_flask_mail(to_email: str, subject: str, html: str, sender: str) -> bool:
    if not mail:
        return False
    try:
        from flask_mail import Message
        with app_context():
            msg = Message(subject=subject, recipients=[to_email], html=html, sender=sender)
            mail.send(msg)
            return True
    except Exception as e:
        logger.error("Flask-Mail send failed: {}", e)
        return False


def process_mail_payload(payload: dict) -> None:
    """payload: {to, subject, html, sender?}"""
    to_email = payload.get("to")
    subject = payload.get("subject") or "PittState Connect"
    html = payload.get("html") or "<p>Hello from PittState Connect</p>"
    sender = payload.get("sender") or os.getenv("MAIL_DEFAULT_SENDER", "noreply@pittstateconnect.com")

    if not to_email:
        logger.warning("mail payload missing 'to': {}", payload)
        return

    # Try SendGrid first
    if sendgrid_client:
        if send_email_via_sendgrid(to_email, subject, html, sender):
            incr_metric("mail.sent")
            logger.info("Sent email via SendGrid -> {}", to_email)
            return

    # Fallback to Flask-Mail
    if send_email_via_flask_mail(to_email, subject, html, sender):
        incr_metric("mail.sent")
        logger.info("Sent email via Flask-Mail -> {}", to_email)
        return

    incr_metric("mail.failed")
    logger.error("All email transports failed -> {}", to_email)


# --- AI tasks ----------------------------------------------------------------
def process_ai_payload(payload: dict) -> None:
    """
    payload example:
    {
      "type": "essay_feedback",
      "student_id": 123,
      "text": "my essay...",
      "model": "gpt-4o-mini"
    }
    or:
    {
      "type": "smart_match_train",
      "dataset": "s3://.../training.csv"
    }
    """
    if not openai:
        logger.warning("AI payload received but OPENAI_API_KEY not configured")
        return

    task_type = payload.get("type")
    model = payload.get("model", "gpt-4o-mini")

    if task_type == "essay_feedback":
        text = payload.get("text", "")
        if not text.strip():
            logger.warning("AI essay_feedback missing text")
            return
        try:
            # Lightweight completion-style API
            rsp = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful scholarship essay mentor."},
                    {"role": "user", "content": f"Give concise, constructive feedback:\n\n{text}"},
                ],
                temperature=0.2,
            )
            feedback = rsp.choices[0].message.content.strip()
            logger.info("AI feedback generated (len={}): {}", len(feedback), feedback[:140] + "…")
            incr_metric("ai.essay_feedback")
            # TODO: persist feedback to DB or send email back to student
        except Exception as e:
            incr_metric("ai.failed")
            logger.error("AI essay feedback failed: {}", e)

    elif task_type == "smart_match_train":
        # Placeholder: orchestrate training job or call fine-tuned embeddings
        try:
            # Example no-op with a log
            logger.info("Smart-match training kicked off with payload: {}", payload)
            incr_metric("ai.smart_match_train")
        except Exception as e:
            incr_metric("ai.failed")
            logger.error("AI smart-match training failed: {}", e)

    else:
        logger.warning("Unknown AI task type: {}", task_type)


# --- Cache warmers ------------------------------------------------------------
def warm_cache_departments():
    try:
        from blueprints.departments.routes import get_departments  # your helper if available
    except Exception:
        get_departments = None

    try:
        with app_context():
            if cache and get_departments:
                _ = get_departments()
                incr_metric("cache.departments.warm")
                logger.info("Departments cache warmed")
    except Exception as e:
        logger.debug("Departments cache warm skipped: {}", e)


def warm_cache_scholarships():
    try:
        from blueprints.scholarships.routes import fetch_scholarships  # if you exposed it
    except Exception:
        fetch_scholarships = None

    try:
        with app_context():
            if cache and fetch_scholarships:
                _ = fetch_scholarships(limit=25)
                incr_metric("cache.scholarships.warm")
                logger.info("Scholarships cache warmed")
    except Exception as e:
        logger.debug("Scholarships cache warm skipped: {}", e)


def warm_cache_careers():
    try:
        from blueprints.careers.routes import fetch_jobs  # if you exposed it
    except Exception:
        fetch_jobs = None

    try:
        with app_context():
            if cache and fetch_jobs:
                _ = fetch_jobs(limit=25)
                incr_metric("cache.careers.warm")
                logger.info("Careers cache warmed")
    except Exception as e:
        logger.debug("Careers cache warm skipped: {}", e)


def run_cache_warmers():
    warm_cache_departments()
    warm_cache_scholarships()
    warm_cache_careers()


# --- Queue loops --------------------------------------------------------------
def brpop_loop(queue_key: str, handler, stop_flag, label: str):
    """Generic BRPOP loop with heartbeat + exponential backoff on connection errors."""
    backoff = 1
    max_backoff = 30

    logger.info("Starting {} loop on Redis key: {}", label, queue_key)
    while stop_flag() and RUNNING:
        heartbeat()
        if not redis_client:
            logger.warning("Redis unavailable; sleeping {}s", backoff)
            time.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)
            continue

        try:
            # BRPOP returns (key, value) or None on timeout
            item = redis_client.brpop(queue_key, timeout=5)
            if item is None:
                # Idle tick
                backoff = 1
                continue

            _, raw = item
            try:
                data = json.loads(raw)
            except Exception:
                data = {"raw": raw}

            with app_context():
                handler(data)

            backoff = 1

        except Exception as e:
            logger.error("{} loop error: {}", label, e)
            time.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)

    logger.info("{} loop exiting", label)


def mail_loop(stop_flag):
    return brpop_loop(MAIL_QUEUE_KEY, process_mail_payload, stop_flag, "MAIL")


def ai_loop(stop_flag):
    return brpop_loop(AI_QUEUE_KEY, process_ai_payload, stop_flag, "AI")


# --- Signal handling ----------------------------------------------------------
def _install_signal_handlers():
    def _graceful(signum, frame):
        global RUNNING
        logger.warning("Signal {} received; shutting down gracefully…", signum)
        RUNNING = False

    signal.signal(signal.SIGINT, _graceful)
    signal.signal(signal.SIGTERM, _graceful)


# --- CLI ----------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="PittState-Connect background worker")
    p.add_argument("--with-mail", action="store_true", help="Enable mail queue processor")
    p.add_argument("--with-ai", action="store_true", help="Enable AI queue processor")
    p.add_argument("--with-cache", action="store_true", help="Run cache warmers on boot and every 30m")
    p.add_argument("--once", action="store_true", help="Process one item per enabled queue then exit")
    p.add_argument("--idle-exit-seconds", type=int, default=0, help="Exit if idle for N seconds (0=never)")
    return p.parse_args()


def main():
    _install_signal_handlers()
    args = parse_args()

    logger.info("Worker starting with flags: mail={}, ai={}, cache={}, once={}, idle_exit={}",
                args.with_mail, args.with_ai, args.with_cache, args.once, args.idle_exit_seconds)

    # Optional cache warmers at boot
    if args.with_cache:
        run_cache_warmers()

    last_activity = time.time()

    def stop_flag():
        if not RUNNING:
            return False
        if args.idle_exit_seconds > 0 and (time.time() - last_activity) > args.idle_exit_seconds:
            logger.info("Idle exit after {}s with no work", args.idle_exit_seconds)
            return False
        return True

    # ONE-SHOT mode (for cron-like usage on Render)
    if args.once:
        if args.with_mail and redis_client:
            item = redis_client.rpop(MAIL_QUEUE_KEY)
            if item:
                last_activity = time.time()
                process_mail_payload(json.loads(item))
        if args.with_ai and redis_client:
            item = redis_client.rpop(AI_QUEUE_KEY)
            if item:
                last_activity = time.time()
                process_ai_payload(json.loads(item))
        if args.with_cache:
            run_cache_warmers()
        logger.info("One-shot mode complete")
        return 0

    # CONTINUOUS mode
    # Simple single-threaded multiplexing to keep the file minimal; add threads if desired.
    try:
        while stop_flag():
            did_work = False

            if args.with_mail and redis_client:
                item = redis_client.rpop(MAIL_QUEUE_KEY)
                if item:
                    did_work = True
                    last_activity = time.time()
                    process_mail_payload(json.loads(item))

            if args.with_ai and redis_client:
                item = redis_client.rpop(AI_QUEUE_KEY)
                if item:
                    did_work = True
                    last_activity = time.time()
                    process_ai_payload(json.loads(item))

            if args.with_cache and int(time.time()) % (30 * 60) == 0:  # every ~30 minutes
                run_cache_warmers()

            heartbeat()

            if not did_work:
                time.sleep(1)

    except Exception as e:
        logger.exception("Worker crashed unexpectedly: {}", e)
        return 1

    logger.info("Worker stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
