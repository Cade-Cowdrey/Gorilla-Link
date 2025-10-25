from flask_mail import Message
from flask import render_template, current_app
from datetime import datetime
from openai import OpenAI
from app_pro import mail, db
from utils.analytics_util import run_usage_analytics
from utils.report_pdf import build_monthly_report_pdf
import os

# --- Weekly Analytics Digest -------------------------------------------------
def send_weekly_analytics_digest(recipient_email, recipient_name="Administrator"):
    """Send PSU-branded weekly analytics + AI insight email digest."""
    try:
        data = run_usage_analytics(db)
        users = data.get("users", 0)
        posts = data.get("posts", 0)
        departments = data.get("departments", 0)
        scholarships = data.get("scholarships", 0)

        ai_text = "Data insights unavailable."
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            prompt = (
                f"Analyze PSU PittState-Connect weekly data: {users} users, {posts} posts, "
                f"{departments} departments, {scholarships} scholarships. "
                "Provide a 1-sentence, upbeat summary suitable for an analytics email."
            )
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a PSU analytics assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=80
            )
            ai_text = completion.choices[0].message.content.strip()

        html_body = render_template(
            "emails/analytics_weekly_digest.html",
            recipient_name=recipient_name,
            generated_at=datetime.utcnow().strftime("%B %d, %Y"),
            users=users, posts=posts,
            departments=departments, scholarships=scholarships,
            ai_insight=ai_text
        )
        text_body = render_template(
            "emails/analytics_weekly_digest.txt",
            recipient_name=recipient_name,
            generated_at=datetime.utcnow().strftime("%B %d, %Y"),
            users=users, posts=posts,
            departments=departments, scholarships=scholarships,
            ai_insight=ai_text
        )

        msg = Message(
            subject="📊 PittState-Connect Weekly Analytics Digest",
            recipients=[recipient_email],
            html=html_body, body=text_body,
            sender=("PittState-Connect", "noreply@pittstate.edu")
        )
        mail.send(msg)
        current_app.logger.info(f"Weekly digest sent to {recipient_email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Weekly digest failed: {e}")
        return False


# --- Monthly Report PDF Sender ----------------------------------------------
def send_monthly_report_pdf(recipient_emails, month, year, department_id=None):
    """Generate & email monthly PDF report."""
    try:
        filename, pdf_bytes, meta = build_monthly_report_pdf(db, month, year, department_id)
        subject = f"📄 PSU Monthly Analytics — {meta['period_label']}"
        body = (
            f"Attached is the PittState-Connect monthly analytics report for {meta['period_label']}.\n\n"
            "— PittState-Connect"
        )
        msg = Message(
            subject=subject,
            recipients=recipient_emails,
            body=body,
            sender=("PittState-Connect", "noreply@pittstate.edu")
        )
        msg.attach(filename, "application/pdf", pdf_bytes)
        mail.send(msg)
        current_app.logger.info(f"[MAIL] Monthly PDF sent to {recipient_emails} ({filename})")
        return True
    except Exception as e:
        current_app.logger.error(f"[MAIL] Monthly PDF send failed: {e}")
        return False
