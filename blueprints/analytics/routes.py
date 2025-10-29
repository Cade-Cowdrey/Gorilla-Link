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
    """Main analytics dashboard."""
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
        logger.error(f"❌ Analytics dashboard failed: {e}")
        return render_template("errors/500.html", title="Server Error"), 500


# ==========================================================
# 🔍 JSON ENDPOINTS (for live charts)
# ==========================================================

@analytics_bp.route("/page-stats")
@login_required
def page_stats_api():
    try:
        return jsonify({"status": "success", "data": get_page_stats(limit=50)})
    except Exception as e:
        logger.error(f"page_stats_api failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/api-stats")
@login_required
def api_stats_api():
    try:
        return jsonify({"status": "success", "data": get_api_stats(limit=50)})
    except Exception as e:
        logger.error(f"api_stats_api failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================================
# ❤️ HEALTH CHECK
# ==========================================================

@analytics_bp.route("/ping")
def ping():
    return {"status": "ok", "module": "analytics"}

# 👇 Required for auto-registration
bp = analytics_bp
