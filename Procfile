# PittState-Connect | Render Production Process File
# Defines all app processes for Render deployment

web: gunicorn app_pro:app --workers=4 --threads=2 --timeout=120 --log-level=info

# Optional background worker for scheduled or async tasks
worker: python worker.py
