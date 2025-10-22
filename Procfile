# =============================================================
# PittState-Connect — Procfile
# Advanced Gunicorn + Flask (factory pattern)
# Supports optional enhancements: AI helper, analytics, mentoring,
# donor portal, and scholarship hub extensions.
# =============================================================

# ------------------------------
# PRIMARY WEB SERVICE
# ------------------------------
web: gunicorn 'app_pro:create_app()' \
      --workers ${GUNICORN_WORKERS:-3} \
      --threads ${GUNICORN_THREADS:-2} \
      --timeout ${GUNICORN_TIMEOUT:-120} \
      --worker-class ${GUNICORN_WORKER_CLASS:-gthread} \
      --access-logfile - \
      --error-logfile - \
      --log-level ${LOG_LEVEL:-info} \
      --preload \
      --bind 0.0.0.0:$PORT

# ------------------------------
# OPTIONAL BACKGROUND WORKER
# Handles asynchronous jobs like:
# - Smart scholarship matching
# - Email reminders
# - Donor analytics sync
# - AI essay scoring queue
# ------------------------------
worker: python worker.py

# ------------------------------
# OPTIONAL TASKS / CRON JOBS
# These are lightweight scheduled jobs triggered by Render Cron.
# Example: Auto-refresh analytics, send weekly mentor summaries.
# ------------------------------
cron: python manage_tasks.py

# ------------------------------
# HEALTH CHECK / DIAGNOSTICS
# Optional script to validate blueprint registration and DB status.
# ------------------------------
diagnostic: python diagnostics/run_check.py

# ------------------------------
# COMMENTED ADVANCED MODES
# Uncomment to enable async worker or enhanced concurrency.
# ------------------------------
# web: gunicorn 'app_pro:create_app()' \
#       --workers 4 \
#       --worker-class gevent \
#       --worker-connections 1000 \
#       --timeout 90 \
#       --access-logfile - \
#       --error-logfile - \
#       --preload
