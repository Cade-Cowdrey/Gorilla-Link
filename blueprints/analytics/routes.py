from flask import Blueprint, render_template
bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

@bp.get("/insights")
def insights():
    return render_template("analytics/insights_dashboard.html")
