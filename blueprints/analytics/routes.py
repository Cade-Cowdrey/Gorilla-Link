from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from utils.analytics_util import get_page_stats, get_api_stats
from loguru import logger

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

# ==========================================================
# 📊 ANALYTICS DASHBOARD
# ==========================================================

@analytics_bp.route("/")
@login_required
def dashboard():
    """
    Displays analytics dashboard (admin/staff only) showing 
    site traffic, popular pages, and API usage stats.
    """
    try:
        page_stats = get_page_stats(limit=20)
        api_stats = get_api_stats(limit=20)

        return render_template(
            "analytics/dashboard.html",
            title="Analytics Dashboard | PittState-Connect",
            page_stats=page_stats,
            api_stats=api_stats,
        )
    except Exception as e:
        logger.error(f"❌ Error rendering analytics dashboard: {e}")
        return render_template(
            "errors/500.html",
            title="Server Error | PittState-Connect"
        ), 500


# ==========================================================
# 🔍 JSON ENDPOINTS (for live charts)
# ==========================================================

@analytics_bp.route("/page-stats")
@login_required
def page_stats_api():
    """
    Returns page view statistics as JSON for dashboard charts.
    """
    try:
        data = get_page_stats(limit=50)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"❌ page_stats_api failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/api-stats")
@login_required
def api_stats_api():
    """
    Returns API endpoint usage stats as JSON for dashboard charts.
    """
    try:
        data = get_api_stats(limit=50)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"❌ api_stats_api failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================================
# ❤️ HEALTH CHECK (internal)
# ==========================================================

@analytics_bp.route("/ping")
def ping():
    return {"status": "ok", "module": "analytics"}
