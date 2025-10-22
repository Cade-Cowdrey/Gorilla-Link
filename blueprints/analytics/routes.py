# ============================================================
# FILE: blueprints/analytics/routes.py
# ============================================================
from flask import render_template, current_app
from . import analytics_bp

@analytics_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if not current_app.config.get("ANALYTICS_DASHBOARD", True):
        return render_template("errors/disabled.html", feature="Analytics Dashboard"), 200
    # Placeholder KPIs; wire to DB later
    kpis = {
        "placement_rate": "87%",
        "scholarships_awarded": 312,
        "active_mentors": 148,
        "engagement_score": 76,
    }
    return render_template("analytics/dashboard.html", kpis=kpis)
