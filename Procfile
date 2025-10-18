# ---------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Full Production Procfile (Web + Worker)
# ---------------------------------------------

# --- Main Flask Web Service ---
web: gunicorn --worker-class gevent --workers 3 --threads 2 --timeout 300 app_pro:create_app()

# --- Background Task Worker ---
# Handles scheduled jobs, email sending, and maintenance tasks
worker: python worker.py
