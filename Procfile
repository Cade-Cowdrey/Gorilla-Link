# ============================================================
# 🦍 PittState-Connect — Production Procfile
# ============================================================

# ────────────────────────────────────────────────────────────
# 🌐 Web Server (Main App)
# Uses Gunicorn to serve the Flask app with preload for speed
# ────────────────────────────────────────────────────────────
web: gunicorn app_pro:app \
    --workers=3 \
    --threads=2 \
    --timeout=120 \
    --preload \
    --log-level=info \
    --access-logfile - \
    --error-logfile -

# ────────────────────────────────────────────────────────────
# ⚙️ Worker (Background Jobs / Mail Queue / AI Tasks)
# Handles async SendGrid email queue, Redis events, and OpenAI tasks
# ────────────────────────────────────────────────────────────
worker: python worker.py --with-mail --with-ai --with-cache

# ────────────────────────────────────────────────────────────
# 🕒 Scheduler (Nightly Analytics, Smart Match, Auto-Reminders)
# Tied into APScheduler via extensions.scheduler
# ────────────────────────────────────────────────────────────
scheduler: python -m tools.run_scheduler

# ────────────────────────────────────────────────────────────
# 📊 Manual Analytics Refresh (fallback job if scheduler fails)
# Can be triggered manually from Render shell:
#   $ render exec python -m blueprints.analytics.tasks refresh_insight_cache
# ────────────────────────────────────────────────────────────
analytics-refresh: python -m blueprints.analytics.tasks refresh_insight_cache

# ────────────────────────────────────────────────────────────
# 📬 Mail Queue Processor
# Processes queued transactional + campaign emails via SendGrid
# ────────────────────────────────────────────────────────────
mail-queue: python -m utils.mail_util process_queue

# ────────────────────────────────────────────────────────────
# 🧠 OpenAI Helper (Essay feedback, Smart-Match training)
# Uses OPENAI_API_KEY from environment
# ────────────────────────────────────────────────────────────
ai-helper: python -m tools.ai_helper run
