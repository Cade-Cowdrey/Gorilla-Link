# blueprints/analytics/routes.py
from __future__ import annotations
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

def _user_role():
    return getattr(current_user, "role", "student")

@analytics_bp.get("/")
@login_required
def index():
    role = _user_role()
    if role in {"admin", "executive"}:
        cards = [
            {"label": "Active Users", "value": 1287, "delta": +4.3},
            {"label": "Scholarships", "value": 52, "delta": +1.0},
            {"label": "Applications", "value": 231, "delta": +7.8},
            {"label": "Job Postings", "value": 88, "delta": -2.1},
        ]
    elif role == "chair":
        cards = [
            {"label": "Dept Users", "value": 214, "delta": +2.2},
            {"label": "Dept Scholarships", "value": 9, "delta": +1.0},
            {"label": "Dept Applications", "value": 41, "delta": +4.1},
        ]
    else:
        cards = [
            {"label": "My Applications", "value": 3, "delta": +1.0},
            {"label": "Recommended Jobs", "value": 6, "delta": +2.0},
        ]
    chart_url = "/static/analytics/active_users.png"
    return render_template("analytics/index.html", cards=cards, chart_url=chart_url, role=role)

@analytics_bp.get("/api/kpis")
@login_required
def kpis():
    data = {
        "kpis": [
            {"label": "Active Users", "value": 1287, "delta": 4.3, "unit": ""},
            {"label": "Scholarships", "value": 52, "delta": 1.0, "unit": ""},
            {"label": "Applications", "value": 231, "delta": 7.8, "unit": ""},
            {"label": "Job Postings", "value": 88, "delta": -2.1, "unit": ""},
        ]
    }
    return jsonify(data)

@analytics_bp.get("/api/series/active-users")
@login_required
def active_users_series():
    return jsonify({"series": [1180, 1192, 1201, 1215, 1228, 1276, 1287]})
