# ==============================================================
# Nightly rollup — snapshot metrics into DailyStats
# ==============================================================
from datetime import date, datetime, timedelta
from app_pro import create_app
from extensions import db
from models import User, Alumni, Faculty, Department, Job, Post, ActivityLog, DailyStats

app = create_app()

with app.app_context():
    today = date.today()
    exists = DailyStats.query.filter_by(date=today).first()
    if not exists:
        # alumni logins in last 24h
        since = datetime.utcnow() - timedelta(days=1)
        alumni_ids = [a.id for a in Alumni.query.with_entities(Alumni.id).all()]
        alumni_logins = (
            db.session.query(ActivityLog)
            .filter(ActivityLog.timestamp >= since, ActivityLog.action.ilike("%login%"))
            .count()
        )

        row = DailyStats(
            date=today,
            users=db.session.query(User).count(),
            alumni=db.session.query(Alumni).count(),
            faculty=db.session.query(Faculty).count(),
            posts=db.session.query(Post).count(),
            jobs=db.session.query(Job).count(),
            alumni_logins=alumni_logins,
        )
        db.session.add(row)
        db.session.commit()
        print("✅ DailyStats row created:", today)
    else:
        print("ℹ️ DailyStats already exists for", today)
