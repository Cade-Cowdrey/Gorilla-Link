# =============================================================
# FILE: diagnostics/run_check.py
# PittState-Connect — System Diagnostics and Health Checker
# Runs on Render (diagnostic process) or locally before deploy.
# Checks blueprints, database, AI config, mail setup, env flags,
# and security settings.
# =============================================================

import os
import sys
import logging
import traceback
from pathlib import Path
from importlib import import_module
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("diagnostic")

# Ensure the app factory and models are available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from app_pro import create_app
    from models import db
except Exception as e:
    log.critical("❌ Could not import app or models: %s", e)
    sys.exit(1)

# =============================================================
# 1️⃣  Create app context
# =============================================================
log.info("🧩 Running PittState-Connect diagnostic checks...")
app = create_app()
app.app_context().push()

# =============================================================
# 2️⃣  Blueprint registration check
# =============================================================
try:
    bp_names = list(app.blueprints.keys())
    log.info("✅ %d blueprints loaded:", len(bp_names))
    for bp in bp_names:
        log.info("   • %s", bp)
except Exception as e:
    log.error("❌ Blueprint check failed: %s", e)

# =============================================================
# 3️⃣  Database connection test
# =============================================================
try:
    db.session.execute("SELECT 1")
    log.info("✅ Database connection: OK")
except Exception as e:
    log.warning("⚠️ Database connection failed: %s", e)

# =============================================================
# 4️⃣  Mail configuration test
# =============================================================
required_mail_vars = ["MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD"]
missing_mail = [v for v in required_mail_vars if not os.getenv(v)]
if missing_mail:
    log.warning("⚠️ Mail not fully configured (missing %s)", ", ".join(missing_mail))
else:
    log.info("✅ Mail configuration appears complete")

# =============================================================
# 5️⃣  AI / OpenAI configuration
# =============================================================
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    log.info("✅ OpenAI key detected — AI helper active")
else:
    log.warning("⚠️ No OPENAI_API_KEY — AI helper disabled")

# =============================================================
# 6️⃣  Feature Flags Summary
# =============================================================
feature_flags = [
    "CAREERS_BOARD_ENABLED",
    "SCHOLARSHIP_HUB_ENABLED",
    "MENTORSHIP_PROGRAM_ENABLED",
    "DONOR_PORTAL_ENABLED",
    "NOTIFICATIONS_ENABLED",
    "DEPARTMENT_PAGES_ENABLED",
    "ANALYTICS_DASHBOARD",
    "ALUMNI_PORTAL_ENABLED",
    "EVENTS_ENABLED",
    "MESSAGING_ENABLED",
]

log.info("📦 Feature Flags:")
for flag in feature_flags:
    val = os.getenv(flag, "False")
    emoji = "🟢" if val.lower() in {"1", "true", "yes", "on"} else "🔴"
    log.info("   %s %s=%s", emoji, flag, val)

# =============================================================
# 7️⃣  Static / Template assets
# =============================================================
paths = ["templates", "static"]
for folder in paths:
    path = Path(folder)
    if path.exists():
        total = sum(1 for _ in path.rglob("*") if _.is_file())
        log.info("✅ %s: %d files", folder, total)
    else:
        log.warning("⚠️ %s folder missing", folder)

# =============================================================
# 8️⃣  Persistent disk & uploads
# =============================================================
persistent_path = Path("/opt/render/project/persistent")
if persistent_path.exists():
    log.info("💾 Persistent storage available at %s", persistent_path)
else:
    log.warning("⚠️ No persistent storage mounted")

# =============================================================
# 9️⃣  Security configuration checks
# =============================================================
security_vars = [
    ("SESSION_COOKIE_SECURE", "True"),
    ("SESSION_COOKIE_SAMESITE", "Lax"),
    ("PREFERRED_URL_SCHEME", "https"),
]
for var, expected in security_vars:
    actual = os.getenv(var, "")
    if actual.lower() != expected.lower():
        log.warning("⚠️ %s is %s (expected %s)", var, actual or "unset", expected)
    else:
        log.info("✅ %s=%s", var, actual)

# =============================================================
# 🔟  Optional service checks
# =============================================================
try:
    from utils.mail_util import send_email

    if callable(send_email):
        log.info("✅ Mail utility callable — ready for outbound messages")
except Exception as e:
    log.warning("⚠️ Could not verify mail utility: %s", e)

# AI model sanity
model = os.getenv("AI_MODEL", "")
if model:
    log.info("✅ AI model configured: %s", model)
else:
    log.info("ℹ️  Default AI model will be used (gpt-4o-mini)")

# =============================================================
# 11️⃣  Final summary
# =============================================================
log.info("🧭 Environment summary:")
log.info("   FLASK_ENV=%s", os.getenv("FLASK_ENV"))
log.info("   LOG_LEVEL=%s", os.getenv("LOG_LEVEL", "info"))
log.info("   DATABASE_URL=%s", ("set" if os.getenv("DATABASE_URL") else "missing"))
log.info("   MAIL_SERVER=%s", os.getenv("MAIL_SERVER", "not set"))
log.info("   TIME=%s UTC", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

# =============================================================
# ✅ Done
# =============================================================
log.info("✅ PittState-Connect diagnostics completed successfully.")
print("\nAll checks finished.\n")
