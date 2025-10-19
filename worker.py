"""
worker.py
------------------------------------------------------------
Background worker for PittState-Connect
------------------------------------------------------------
• Sends weekly Jungle Digest emails
• Generates analytics + engagement reports
• Cleans up expired notifications
• Runs in parallel to main Flask web service
------------------------------------------------------------
"""

from datetime import datetime, timedelta
import time
from flask import Flask
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from redis import Redis
import os
import traceback
from rich.console import Console

console = Console()


# ==========================================================
# 🦍 Flask App Context Setup
# ==========================================================
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = (
    "PittState-Connect",
    os.getenv("MAIL_USERNAME", "noreply@pittstate.edu"),
)

# ==========================================================
# ⚙️ Extensions
# ==========================================================
db = SQLAlchemy(app)
mail = Mail(app)
cache = Cache(config={"CACHE_TYPE": "RedisCache", "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0")})
cache.init_app(app)
scheduler = APScheduler()
scheduler.init_app(app)

try:
    redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
except Exception as e:
    console.print(f"[red]⚠️ Redis connection failed:[/red] {e}")
    redis_client = None


# ==========================================================
# 📦 Models (minimal subset for worker tasks)
# ==========================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    is_alumni = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class EmailDigestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(120))
    subject = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="sent")


# ==========================================================
# 📬 Weekly Digest Sender
# ==========================================================
def send_weekly_digest():
    """Send Jungle Digest emails to all verified users (weekly)"""
    with app.app_context():
        try:
            users = User.query.filter(User.email.isnot(None)).all()
            if not users:
                console.print("[yellow]⚠️ No users found for digest.[/yellow]")
                return

            sent_count = 0
            for user in users:
                msg = Message(
                    subject="🌴 Jungle Digest — Weekly Highlights from PittState-Connect",
                    recipients=[user.email],
                    html=f"""
                    <h2 style='color:#DAA520;'>Hi {user.first_name or 'Gorilla'},</h2>
                    <p>Here's your weekly roundup of new events, jobs, and alumni stories.</p>
                    <p><a href='https://pittstate-connect.onrender.com'>Open PittState-Connect</a></p>
                    <p style='color:gray;font-size:12px;'>You’re receiving this email because you’re part of the Gorilla Network.</p>
                    """,
                )
                mail.send(msg)
                log = EmailDigestLog(recipient_email=user.email, subject=msg.subject, status="sent")
                db.session.add(log)
                sent_count += 1

            db.session.commit()
            console.print(f"[green]✅ Sent {sent_count} Jungle Digest emails.[/green]")
        except Exception as e:
            db.session.rollback()
            console.print(f"[red]❌ Error sending digest:[/red] {e}")
            traceback.print_exc()


# ==========================================================
# 🧹 Notification Cleanup
# ==========================================================
def cleanup_old_notifications():
    """Deletes notifications older than 60 days."""
    with app.app_context():
        try:
            cutoff = datetime.utcnow() - timedelta(days=60)
            old = Notification.query.filter(Notification.created_at < cutoff).all()
            count = len(old)
            for n in old:
                db.session.delete(n)
            db.session.commit()
            if count:
                console.print(f"[blue]🧹 Cleaned up {count} old notifications.[/blue]")
        except Exception as e:
            db.session.rollback()
            console.print(f"[red]❌ Error cleaning notifications:[/red] {e}")


# ==========================================================
# 📊 Analytics Summary
# ==========================================================
def generate_analytics_snapshot():
    """Caches current platform metrics every 24h."""
    with app.app_context():
        try:
            total_users = User.query.count()
            alumni = User.query.filter_by(is_alumni=True).count()
            cache.set("analytics:users", total_users, timeout=86400)
            cache.set("analytics:alumni", alumni, timeout=86400)
            console.print(
                f"[cyan]📈 Analytics snapshot updated: {total_users} users, {alumni} alumni.[/cyan]"
            )
        except Exception as e:
            console.print(f"[red]❌ Error generating analytics:[/red] {e}")


# ==========================================================
# 🕒 Scheduler Setup
# ==========================================================
scheduler.add_job(id="weekly_digest", func=send_weekly_digest, trigger="interval", days=7)
scheduler.add_job(id="cleanup_notifications", func=cleanup_old_notifications, trigger="interval", days=1)
scheduler.add_job(id="daily_analytics", func=generate_analytics_snapshot, trigger="interval", hours=24)


# ==========================================================
# 🚀 Worker Start
# ==========================================================
if __name__ == "__main__":
    with app.app_context():
        console.print("[bold gold3]🦍 Starting PittState-Connect background worker...[/bold gold3]")
        try:
            scheduler.start()
            console.print("[green]✅ APScheduler started successfully.[/green]")
            while True:
                time.sleep(60)  # Keeps container alive
        except (KeyboardInterrupt, SystemExit):
            console.print("[yellow]⚠️ Worker shutting down...[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Worker error:[/red] {e}")
            traceback.print_exc()
