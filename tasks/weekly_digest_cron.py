# tasks/weekly_digest_cron.py
"""
Render Cron runner:
- Loads Flask app context
- Sends weekly digest to all PSU-domain users
"""

from app_pro import app, db
from utils.mail_util import send_weekly_digest_to_all_psu

if __name__ == "__main__":
    with app.app_context():
        sent, skipped = send_weekly_digest_to_all_psu()
        # Simple console logging for Render logs
        print(f"[WeeklyDigest] Sent={sent} Skipped={skipped}")
