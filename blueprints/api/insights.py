# ==============================================================
# Insights API — summary & timeseries for dashboards
# ==============================================================
from datetime import date, timedelta, datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from extensions import cache, db
from models import User, Alumni, Faculty, Department, Job, Post, ActivityLog, DailyStats

bp = Blueprint("insights", __name__, url_prefix="/api/insights")

@bp.get("/summary")
@cache.cached(timeout=3600)
def summary():
    return jsonify({
        "users": db.session.query(User).count(),
        "alumni": db.session.query(Alumni).count(),
        "faculty": db.session.query(Faculty).count(),
        "departments": db.session.query(Department).count(),
        "jobs": db.session.query(Job).count(),
        "posts": db.session.query(Post).count(),
    })

@bp.get("/timeseries/daily")
@cache.cached(timeout=3600, query_string=True)
def timeseries_daily():
    days = int(request.args.get("days", 30))
    cut = date.today() - timedelta(days=days)
    rows = (
        db.session.query(DailyStats)
        .filter(DailyStats.date >= cut)
        .order_by(DailyStats.date.asc())
        .all()
    )
    data = [
        {
            "date": r.date.isoformat(),
            "users": r.users,
            "alumni": r.alumni,
            "faculty": r.faculty,
            "posts": r.posts,
            "jobs": r.jobs,
            "alumni_logins": r.alumni_logins,
        }
        for r in rows
    ]
    return jsonify(data)
