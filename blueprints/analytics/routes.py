from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from utils.analytics_util import get_page_stats, record_api_usage
from extensions import limiter

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.route("/")
@limiter.limit("15/minute")
@login_required
def dashboard():
    record_api_usage("/analytics", "GET", current_user.id)
    stats = get_page_stats(7)
    return render_template("analytics/dashboard.html", stats=stats, title="Analytics | PittState-Connect")

@bp.route("/api/summary")
@login_required
def api_summary():
    record_api_usage("/analytics/api/summary", "GET", current_user.id)
    return jsonify({"summary": get_page_stats(7)})
