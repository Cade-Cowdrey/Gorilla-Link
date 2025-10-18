# ---------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Production Procfile (Gunicorn + Gevent)
# ---------------------------------------------
web: gunicorn --worker-class gevent --workers 3 --threads 2 --timeout 300 app_pro:create_app()
