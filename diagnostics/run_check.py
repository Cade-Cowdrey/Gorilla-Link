# =============================================================
# FILE: diagnostics/run_check.py
# PittState-Connect — System Health & Blueprint Diagnostic Tool
# -------------------------------------------------------------
# Run via:  python diagnostics/run_check.py
# or:       render.yaml -> service: diagnostic
# -------------------------------------------------------------
# Performs end-to-end verification of:
#   ✅ App factory integrity
#   ✅ Blueprint registration
#   ✅ Database connectivity
#   ✅ Email system readiness
#   ✅ OpenAI / AI helper status
#   ✅ Environment sanity
# =============================================================

import os
import sys
import traceback
import logging
from datetime import datetime

from app_pro import create_app
from models import db
from utils.mail_util import send_email

# Optional: AI & monitoring
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
# LOGGING SETUP
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | diagnostics | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("diagnostics")


# -------------------------------------------------------------
# INITIALIZE APP CONTEXT
# -------------------------------------------------------------
def boot_app():
    try:
        app = create_app()
        app.app_context().push()
        log.info("🦍 PittState-Connect app factory created successfully.")
        return app
    except Exception as e:
        log.exception("❌ Failed to initialize Flask app: %s", e)
        raise


# -------------------------------------------------------------
# CHECK BLUEPRINTS
# -------------------------------------------------------------
def check_blueprints(app):
    try:
        blueprints = list(app.blueprints.keys())
        log.info("📁 Registered Blueprints: %s", blueprints)
        expected = [
            "core_bp", "auth_bp", "careers_bp", "departments_bp",
            "scholarships_bp", "mentors_bp", "alumni_bp",
            "analytics_bp", "donor_bp", "emails_bp", "notifications_bp"
        ]
        missing = [bp for bp in expected if bp not in blueprints]
        if missing:
            log.warning("⚠️ Missing blueprints: %s", missing)
        else:
            log.info("✅ All expected blueprints registered.")
    except Exception as e:
        log.exception("❌ Blueprint check failed: %s", e)


# -------------------------------------------------------------
# DATABASE CHECK
# -------------------------------------------------------------
def check_database():
    try:
        with db.engine.connect() as conn:
            conn.execute("SELECT 1")
        log.info("✅ Database connection successful.")
    except Exception as e:
        log.exception("❌ Database connection failed: %s", e)


# -------------------------------------------------------------
# EMAIL SYSTEM CHECK
# -------------------------------------------------------------
def check_email_system():
    try:
        if not os.getenv("MAIL_SERVER"):
            log.warning("⚠️ MAIL_SERVER not set — email disabled.")
            return
        # Safe dry run (does not actually send)
        send_email(
            subject="[Diagnostics] PittState-Connect Test",
            recipients=[os.getenv("ADMIN_EMAIL", "admin@pittstate.edu")],
            body="This is a diagnostics test email (dry-run).",
            dry_run=True,
        )
        log.info("✅ Email configuration appears valid.")
    except Exception as e:
        log.exception("❌ Email system check failed: %s", e)


# -------------------------------------------------------------
# OPENAI CHECK
# -------------------------------------------------------------
def check_openai():
    try:
        if not openai or not os.getenv("OPENAI_API_KEY"):
            log.info("🧠 OpenAI integration not configured (skipping).")
            return
        openai.api_key = os.getenv("OPENAI_API_KEY")
        log.info("🧠 OpenAI API key detected — testing minimal request...")
        result = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Respond with the word OK."}],
            max_tokens=3,
            temperature=0.1,
        )
        reply = result["choices"][0]["message"]["content"].strip()
        log.info("✅ OpenAI API test successful: %s", reply)
    except Exception as e:
        log.exception("❌ OpenAI test failed: %s", e)


# -------------------------------------------------------------
# ENVIRONMENT CHECK
# -------------------------------------------------------------
def check_environment():
    required = ["SQLALCHEMY_DATABASE_URI", "SECRET_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        log.warning("⚠️ Missing critical env vars: %s", missing)
    else:
        log.info("✅ Core environment variables set.")
    log.info("🌍 FLASK_ENV = %s", os.getenv("FLASK_ENV", "production"))
    log.info("📦 RENDER = %s", os.getenv("RENDER", "local"))


# -------------------------------------------------------------
# SENTRY CHECK
# -------------------------------------------------------------
def check_sentry():
    if SENTRY_ENABLED and os.getenv("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            integrations=[FlaskIntegration()],
            environment=os.getenv("FLASK_ENV", "production"),
        )
        log.info("🧩 Sentry enabled — reporting test event.")
        sentry_sdk.capture_message("PittState-Connect Diagnostics Check")
    else:
        log.info("Sentry disabled or DSN missing.")


# -------------------------------------------------------------
# MASTER DIAGNOSTIC RUNNER
# -------------------------------------------------------------
def run_all_diagnostics():
    start_time = datetime.utcnow()
    log.info("🚀 Starting PittState-Connect System Diagnostic (%s)", start_time)

    app = boot_app()
    check_environment()
    check_blueprints(app)
    check_database()
    check_email_system()
    check_openai()
    check_sentry()

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    log.info("✅ All diagnostics completed successfully in %.2fs", elapsed)


# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        run_all_diagnostics()
    except Exception as e:
        log.error("❌ Diagnostics failed: %s", e)
        traceback.print_exc()
        sys.exit(1)
    finally:
        log.info("🏁 Diagnostics finished at %s", datetime.utcnow())
