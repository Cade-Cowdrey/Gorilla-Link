from flask import (
    Blueprint, render_template, jsonify, request, flash, redirect, url_for
)
from flask_login import login_required, current_user
from extensions import db
from models import User, Department, Event, Post, Notification
from datetime import datetime, timedelta

analytics = Blueprint("analytics", __name__, template_folder="templates")

# ----------------------------------------
# 📈 ANALYTICS DASHBOARD
# ----------------------------------------
@analytics.route("/dashboard")
@login_required
def dashboard():
    """
    Main analytics dashboard for admins or authorized users.
    Displays key PittState-Connect performance metrics.
    """
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_events = Event.query.count()
    total_notifications = Notification.query.count()

    students = User.query.filter_by(role="student").count()
    alumni = User.query.filter_by(role="alumni").count()
    faculty = User.query.filter_by(role="faculty").count()

    departments = Department.query.count()
    recent_events = Event.query.order_by(Event.start_date.desc()).limit(5).all()

    return render_template(
        "analytics/analytics_dashboard.html",
        total_users=total_users,
        total_posts=total_posts,
        total_events=total_events,
        total_notifications=total_notifications,
        students=students,
        alumni=alumni,
        faculty=faculty,
        departments=departments,
        recent_events=recent_events,
    )


# ----------------------------------------
# 💡 INSIGHTS DASHBOARD
# ----------------------------------------
@analytics.route("/insights")
@login_required
def insights():
    """
    Provides detailed breakdown of user engagement, departmental activity,
    and event participation trends.
    """
    users = User.query.all()
    departments = Department.query.all()
    events = Event.query.all()

    department_data = []
    for d in departments:
        member_count = len(d.users) if hasattr(d, "users") else 0
        post_count = Post.query.filter_by(department_id=d.id).count()
        department_data.append({
            "name": d.name,
            "members": member_count,
            "posts": post_count,
        })

    total_users = len(users)
    total_posts = Post.query.count()
    total_events = len(events)

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.filter(Event.start_date >= datetime.utcnow()).limit(5).all()

    return render_template(
        "analytics/insights_dashboard.html",
        total_users=total_users,
        total_posts=total_posts,
        total_events=total_events,
        department_data=department_data,
        recent_users=recent_users,
        upcoming_events=upcoming_events,
    )


# ----------------------------------------
# 🧮 JSON DATA ENDPOINTS
# ----------------------------------------
@analytics.route("/data/users")
@login_required
def user_data():
    """Returns JSON data for user growth trends (for charts)."""
    today = datetime.utcnow()
    data = []
    for i in range(6, -1, -1):  # Past 7 days
        day = today - timedelta(days=i)
        count = User.query.filter(
            db.func.date(User.created_at) == day.date()
        ).count()
        data.append({"date": day.strftime("%b %d"), "registrations": count})
    return jsonify(data)


@analytics.route("/data/posts")
@login_required
def post_data():
    """Returns JSON data for posts per department (for pie charts)."""
    departments = Department.query.all()
    result = [
        {"department": d.name, "posts": Post.query.filter_by(department_id=d.id).count()}
        for d in departments
    ]
    return jsonify(result)


@analytics.route("/data/events")
@login_required
def event_data():
    """Returns JSON data for events created and attendance stats."""
    events = Event.query.order_by(Event.start_date.desc()).limit(10).all()
    return jsonify([
        {
            "title": e.title,
            "date": e.start_date.strftime("%b %d"),
            "participants": getattr(e, "attendees_count", 0)
        } for e in events
    ])


# ----------------------------------------
# 🌍 PUBLIC CAMPUS NUMBERS PAGE
# ----------------------------------------
@analytics.route("/campus-numbers")
def campus_numbers_public():
    """
    Public analytics page showing PittState-Connect engagement highlights.
    """
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_events = Event.query.count()
    total_departments = Department.query.count()

    return render_template(
        "campus/numbers_public.html",
        total_users=total_users,
        total_posts=total_posts,
        total_events=total_events,
        total_departments=total_departments,
    )


# ----------------------------------------
# 🧭 REDIRECT HELPERS
# ----------------------------------------
@analytics.route("/")
def analytics_root():
    """Redirect base /analytics route to main dashboard."""
    return redirect(url_for("analytics.dashboard"))
