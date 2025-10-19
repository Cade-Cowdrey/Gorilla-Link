from flask import Blueprint, render_template

analytics_bp = Blueprint("analytics", __name__, template_folder="templates/analytics")

@analytics_bp.route("/analytics/insights")
def analytics_insights():
    """PSU analytics dashboard — campus, alumni, and student engagement stats."""
    return render_template("analytics/insights_dashboard.html", title="Analytics Insights | PittState-Connect")
