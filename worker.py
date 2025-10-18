# ==============================================================
# Gorilla-Link Background Worker
# Handles analytics updates, digest emails, and cleanup tasks
# Now includes persistent logging to /logs/worker.log
# ==============================================================

import os
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from extensions import db
from models import User, Notification, DailyStats, Alumni
from app_pro import create_app

# --------------------------------------------------------------
# Setup Logging
# --------------------------------------------------------------
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "worker.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # also print to Render logs
    ]
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------
# Initialize App Context
# --------------------------------------------------------------
app = create_app()
mail = Mail(app)
scheduler = APScheduler()

# --------------------------------------------------------------
# 📊 Analytics: Update Daily Stats
# --------------------------------------------------------------
def update_daily_stats():
    with app.app_context():
        try:
            today = datetime.utcnow().date()
            users = User.query.count()
            alumni = Alumni.query.count()
            total_notifications = Notification.query.count()

            stats = DailyStats.query.filter_by(date=today).first()
            if not stats:
                stats = DailyStats(date=today)

            stats.users = users
            stats.alumni = alumni
            stats.posts = 0
            stats.jobs = 0
            stats.alumni_logins = total_notifications

            db.session.add(stats)
            db.session.commit()

            logger.info(f"✅ DailyStats updated: users={users}, alumni={alumni}")
        except Exception as e:
            logger.error(f"❌ Failed to update DailyStats: {e}")

# --------------------------------------------------------------
# 📬 Email: Send Weekly Alumni Digest
# --------------------------------------------------------------
def send_alumni_digest():
    with app.app_context():
        try:
            alumni = Alumni.query.limit(50).all()
            for alum in alumni:
                if not alum.email:
                    continue
                msg = Message(
                    subject="Your Weekly Pitt State Alumni Digest",
                    recipients=[alum.email],
                    html=f"""
                    <h2>Gorilla-Link Digest</h2>
                    <p>Hello {alum.name},</p>
                    <p>Stay connected! Check out the latest alumni updates and student posts.</p>
                    <p><a href="https://gorilla-link.onrender.com">Visit Gorilla-Link</a></p>
                    """,
                )
                try:
                    mail.send(msg)
                    logger.info(f"📧 Sent digest to {alum.email}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send to {alum.email}: {e}")
        except Exception as e:
            logger.error(f"❌ Error in send_alumni_digest: {e}")

# --------------------------------------------------------------
# 🧹 Cleanup: Remove old notifications
# --------------------------------------------------------------
def cleanup_notifications():
    with app.app_context():
        try:
            cutoff = datetime.utcnow() - timedelta(days=60)
            old = Notification.query.filter(Notification.sent_at < cutoff).all()
            count = len(old)
            for n in old:
                db.session.delete(n)
            db.session.commit()
            logger.info(f"🧹 Cleaned up {count} old notifications.")
        except Exception as e:
            logger.error(f"❌ Failed to clean notifications: {e}")

# --------------------------------------------------------------
# 🕒 Scheduler Configuration
# --------------------------------------------------------------
scheduler.add_job(id="update_daily_stats", func=update_daily_stats, trigger="interval", hours=24)
scheduler.add_job(id="send_alumni_digest", func=send_alumni_digest, trigger="interval", days=7)
scheduler.add_job(id="cleanup_notifications", func=cleanup_notifications, trigger="interval", days=3)

scheduler.init_app(app)
scheduler.start()

# --------------------------------------------------------------
# Run Worker
# --------------------------------------------------------------
if __name__ == "__main__":
    logger.info("🚀 Starting Gorilla-Link Worker...")
    with app.app_context():
        update_daily_stats()
    scheduler.start()
    app.run()
