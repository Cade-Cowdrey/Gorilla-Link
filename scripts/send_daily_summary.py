import os, io, csv, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from app_pro import create_app
from extensions import db
from models import User, Department, Faculty, Alumni, Job, Post, ActivityLog

load_dotenv(".env.production")

def gather_stats():
    now = datetime.utcnow()
    day = now - timedelta(days=1)
    week = now - timedelta(days=7)
    stats = {
        "users_total": db.session.query(User).count(),
        "new_users": db.session.query(User).filter(User.joined_at >= day).count(),
        "alumni": db.session.query(Alumni).count(),
        "faculty": db.session.query(Faculty).count(),
        "departments": db.session.query(Department).count(),
        "jobs": db.session.query(Job).count() if "Job" in globals() else 0,
        "posts": db.session.query(Post).count() if "Post" in globals() else 0,
        "activity_7d": db.session.query(ActivityLog).filter(ActivityLog.timestamp >= week).count() if "ActivityLog" in globals() else 0
    }

    # Collect engagement trend (alumni logins per day)
    trend = []
    for i in range(7):
        start = now - timedelta(days=i+1)
        end = now - timedelta(days=i)
        count = db.session.query(ActivityLog).filter(
            ActivityLog.timestamp >= start,
            ActivityLog.timestamp < end,
            ActivityLog.action.like("%login%")
        ).count()
        trend.append((start.strftime("%a"), count))
    stats["trend"] = list(reversed(trend))
    return stats

def build_chart(stats):
    trend = stats.get("trend", [])
    fig, ax = plt.subplots(figsize=(7,4))
    ax.bar(["Users","Alumni","Faculty","Depts","Jobs","Posts"],
           [stats["users_total"], stats["alumni"], stats["faculty"],
            stats["departments"], stats["jobs"], stats["posts"]],
           color="#660000", alpha=0.7)
    ax2 = ax.twinx()
    if trend:
        days, vals = zip(*trend)
        ax2.plot(days, vals, color="#C7A008", marker="o", label="Alumni Engagement (7d)")
        ax2.set_ylabel("Logins", color="#C7A008")
    ax.set_ylabel("Totals")
    ax.set_title("Gorilla-Link KPIs + 7-Day Alumni Trend")
    ax.set_facecolor("#f8f8f8")
    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return buf.read()

def build_csv(stats):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Metric","Value"])
    for k,v in stats.items():
        if k != "trend":
            w.writerow([k,v])
    if "trend" in stats:
        w.writerow([])
        w.writerow(["Day","Alumni Logins"])
        for d,c in stats["trend"]:
            w.writerow([d,c])
    buf.seek(0)
    return buf.getvalue()

def send_email(subject, html, recipients, csv_data=None, chart_img=None):
    sender = os.getenv("MAIL_DEFAULT_SENDER","PittState Connect <noreply@pittstate.edu>")
    user, pwd = os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD")
    server, port = os.getenv("MAIL_SERVER","smtp.gmail.com"), int(os.getenv("MAIL_PORT","587"))
    ctx = ssl.create_default_context()

    msg = MIMEMultipart("mixed")
    msg["Subject"], msg["From"], msg["To"] = subject, sender, ", ".join(recipients)
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html,"html"))
    msg.attach(alt)

    if csv_data:
        part = MIMEApplication(csv_data, Name="dashboard_summary.csv")
        part["Content-Disposition"] = "attachment; filename=dashboard_summary.csv"
        msg.attach(part)
    if chart_img:
        img = MIMEImage(chart_img, Name="summary_chart.png")
        img["Content-Disposition"] = "attachment; filename=summary_chart.png"
        msg.attach(img)

    with smtplib.SMTP(server, port) as s:
        s.starttls(context=ctx)
        s.login(user, pwd)
        s.sendmail(sender, recipients, msg.as_string())

def build_and_send_daily_summary(app=None):
    app = app or create_app()
    with app.app_context():
        stats = gather_stats()
        html = f"""
        <html><body style='font-family:Arial'>
        <h2 style='color:#660000'>Gorilla-Link Daily Summary</h2>
        <p>Date: {datetime.utcnow().strftime('%B %d, %Y')}</p>
        <ul>
          <li><b>Total Users:</b> {stats['users_total']}</li>
          <li><b>New Users (24h):</b> {stats['new_users']}</li>
          <li><b>Total Alumni:</b> {stats['alumni']}</li>
          <li><b>Total Faculty:</b> {stats['faculty']}</li>
          <li><b>Departments:</b> {stats['departments']}</li>
          <li><b>Jobs:</b> {stats['jobs']}</li>
          <li><b>Posts:</b> {stats['posts']}</li>
          <li><b>Activity (7d):</b> {stats['activity_7d']}</li>
        </ul>
        <p><b>Weekly Alumni Engagement Trend:</b></p>
        <table border='1' cellpadding='6' style='border-collapse:collapse'>
        <tr><th>Day</th><th>Logins</th></tr>
        {''.join(f'<tr><td>{d}</td><td>{c}</td></tr>' for d,c in stats['trend'])}
        </table>
        <p>Attachments include a CSV summary and chart image.</p>
        </body></html>
        """

        recipients = [r.strip() for r in os.getenv("DASHBOARD_SUMMARY_RECIPIENTS","").split(",") if r.strip()] \
            or [os.getenv("ADMIN_EMAIL","admin@example.com")]

        csv_data = build_csv(stats) if os.getenv("SUMMARY_SEND_CSV","True").lower()=="true" else None
        chart_img = build_chart(stats) if os.getenv("SUMMARY_SEND_CHART","True").lower()=="true" else None

        subject = f"Gorilla-Link Summary • {datetime.utcnow().strftime('%b %d, %Y')}"
        send_email(subject, html, recipients, csv_data, chart_img)
        print(f"✅ Summary sent to: {', '.join(recipients)}")
        return recipients

if __name__ == "__main__":
    build_and_send_daily_summary(None)
