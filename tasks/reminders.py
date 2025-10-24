# tasks/reminders.py
# ===============================================================
#  PittState-Connect Automated Tasks
#  ---------------------------------------------------------------
#  Handles:
#   • Daily Digest generation and (optional) emailing
#   • Scholarship + Event deadline reminders
#   • Logging + graceful error handling
# ===============================================================

from __future__ import annotations
import os, traceback
from datetime import datetime, timedelta
from flask import current_app
from jinja2 import Template

# ---------------------------------------------------------------
#  Email Utility (uses Flask-Mail if configured)
# ---------------------------------------------------------------
def send_email_stub(to: str, subject: str, html: str):
    """Send email via Flask-Mail if available, otherwise log only."""
    try:
        mail = current_app.extensions.get("mail")
        if mail:
            from flask_mail import Message
            msg = Message(subject=subject, recipients=[to], html=html)
            mail.send(msg)
            current_app.logger.info(f"[MAIL] Sent '{subject}' → {to}")
        else:
            current_app.logger.info(f"[MAIL-STUB] Would send to {to}: {subject} ({len(html)} bytes)")
    except Exception as e:
        current_app.logger.error(f"[MAIL-ERROR] {e}")
        traceback.print_exc()

# ---------------------------------------------------------------
#  Daily Campus Digest Job
# ---------------------------------------------------------------
def run_daily_digest_job(app):
    """Generate and email the PittState Daily Digest."""
    with app.app_context():
        try:
            from blueprints.digests.routes import _summarize_posts

            # Fetch your latest data from DB here — sample placeholders
            posts = [
                {"title": "Gorilla Fest Tomorrow!", "summary": "Join us at the Oval for games and food!", "likes": 54, "comments": 9, "tags": ["events", "studentlife"]},
                {"title": "Career Fair This Friday", "summary": "Over 120 employers attending!", "likes": 72, "comments": 15, "tags": ["careers", "networking"]},
            ]
            jobs = [{"title": "Marketing Intern", "company": "Pittsburg Area Chamber"}, {"title": "Software Engineer Co-op", "company": "Kansas City Tech"}]
            events = [{"title": "Homecoming Parade", "when": "Sat 10 AM"}, {"title": "Scholarship Workshop", "when": "Wed 3 PM"}]

            summary = _summarize_posts(posts)
            digest_html = Template("""
                <h2 style='color:#a6192e;font-family:Inter,sans-serif;'>PittState Daily Digest</h2>
                <p><strong>{{date}}</strong> — {{takeaway}}</p>
                <ul>
                  {% for p in posts %}<li><strong>{{p.title}}</strong>: {{p.summary}}</li>{% endfor %}
                </ul>
                <p><strong>Featured Jobs:</strong></p>
                <ul>{% for j in jobs %}<li>{{j.title}} — {{j.company}}</li>{% endfor %}</ul>
                <p><strong>Upcoming Events:</strong></p>
                <ul>{% for e in events %}<li>{{e.title}} — {{e.when}}</li>{% endfor %}</ul>
            """).render(
                date=datetime.utcnow().strftime("%B %d, %Y"),
                takeaway=summary["takeaway"],
                posts=summary["top_posts"],
                jobs=jobs,
                events=events,
            )

            recipients = os.getenv("DIGEST_TO", "admin@pittstate.edu").split(",")
            for r in recipients:
                send_email_stub(r.strip(), "PittState-Connect Daily Digest", digest_html)

            current_app.logger.info("✅ Daily Digest task completed successfully")

        except Exception as e:
            current_app.logger.error(f"❌ Daily Digest failed: {e}")
            traceback.print_exc()

# ---------------------------------------------------------------
#  Scholarship / Event Deadline Reminder Job
# ---------------------------------------------------------------
def run_deadline_reminders_job(app):
    """Scan upcoming deadlines and send reminder emails."""
    with app.app_context():
        try:
            # TODO: Replace with real database queries
            deadlines = [
                {"user": "student1@pittstate.edu", "label": "Business Leadership Scholarship", "due": datetime.utcnow() + timedelta(hours=30)},
                {"user": "student2@pittstate.edu", "label": "Financial Aid Verification", "due": datetime.utcnow() + timedelta(hours=42)},
            ]

            for d in deadlines:
                html = Template("""
                    <p style='font-family:Inter,sans-serif;font-size:15px;color:#1a1a1a'>
                      Reminder from <strong>PittState-Connect</strong> 🦍<br><br>
                      <strong>{{label}}</strong> is due by
                      <span style='color:#a6192e;'>{{due}}</span>.
                      <br><br>Submit before the deadline to stay eligible!
                    </p>
                """).render(label=d["label"], due=d["due"].strftime("%A, %B %d at %I:%M %p UTC"))
                send_email_stub(d["user"], f"Reminder: {d['label']} Deadline Approaching", html)

            current_app.logger.info("✅ Deadline reminders sent successfully")

        except Exception as e:
            current_app.logger.error(f"❌ Deadline reminders failed: {e}")
            traceback.print_exc()

# ---------------------------------------------------------------
#  Manual test helper
# ---------------------------------------------------------------
if __name__ == "__main__":
    # For local testing:  python tasks/reminders.py
    class DummyApp:
        extensions = {}
        logger = type("L", (), {"info": print, "error": print})()
        def app_context(self): from contextlib import nullcontext; return nullcontext()

    app = DummyApp()
    run_daily_digest_job(app)
    run_deadline_reminders_job(app)
