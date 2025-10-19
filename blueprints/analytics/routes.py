# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Analytics Blueprint — PSU Dashboard Insights
# ---------------------------------------------------------
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import User, Department, Post, Event

analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/analytics",
    template_folder="templates"
)

# ---------------------------------------------------------
# Analytics Dashboard (PSU Insights)
# ---------------------------------------------------------
@analytics_bp.route("/dashboard")
@login_required
def dashboard():
    users_count = User.query.count()
    departments_count = Department.query.count()
    posts_count = Post.query.count()
    events_count = Event.query.count()

    return render_template(
        "analytics/insights_dashboard.html",
        title="Analytics Dashboard | PittState-Connect",
        users_count=users_count,
        departments_count=departments_count,
        posts_count=posts_count,
        events_count=events_count,
    )

# ---------------------------------------------------------
# API Endpoint for Metrics
# ---------------------------------------------------------
@analytics_bp.route("/api/metrics")
@login_required
def api_metrics():
    data = {
        "users": User.query.count(),
        "departments": Department.query.count(),
        "posts": Post.query.count(),
        "events": Event.query.count(),
    }
    return jsonify(data)

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@analytics_bp.route("/ping")
def ping():
    return "🦍 Analytics Blueprint active and healthy!"
