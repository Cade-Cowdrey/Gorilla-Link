"""
PittState-Connect | Analytics Blueprint
Provides system-wide insights: user engagement, API usage, and page trends.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from loguru import logger
from extensions import db, redis_client
from utils.analytics_util import get_page_stats, record_api_usage
from models import User, PageView, ApiUsage, Department

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


# ======================================================
# 🧠 DASHBOARD VIEW (Admin Only)
# ======================================================
@bp.route("/")
@login_required
def analytics_dashboard():
    """Displays a live PSU analytics overview dashboard."""
    if current_user.role not in ("admin", "faculty", "staff"):
        return render_template("errors/403.html"), 403

    try:
        # Page stats (cached)
        page_stats = get_page_stats(days=7)

        # Basic user counts
        total_users = User.query.count()
        total_departments = Department.query.count()
        total_views = db.session.query(PageView).count()
        total_api_calls = db.session.query(ApiUsage).count()

        # Most popular pages (top 5)
        popular_pages = sorted(page_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        return render_template(
            "analytics/dashboard.html",
            total_users=total_users,
            total_departments=total_departments,
            total_views=total_views,
            total_api_calls=total_api_calls,
            popular_pages=popular_pages,
            page_stats=page_stats,
        )

    except Exception as e:
        logger.error(f"❌ Analytics dashboard load failed: {e}")
        return render_template("errors/500.html"), 500


# ======================================================
# 📊 JSON ENDPOINT (API)
# ======================================================
@bp.route("/api/summary")
@login_required
def analytics_summary():
    """Returns analytics metrics for admin dashboards in JSON."""
    try:
        record_api_usage("/analytics/api/summary", "GET", user_id=current_user.id)

        cutoff = datetime.utcnow() - timedelta(days=7)

        # Query summaries
        page_views = PageView.query.filter(PageView.timestamp >= cutoff).count()
        api_calls = ApiUsage.query.filter(ApiUsage.timestamp >= cutoff).count()
        new_users = User.query.filter(User.created_at >= cutoff).count()

        data = {
            "period": "last_7_days",
            "page_views": page_views,
            "api_calls": api_calls,
            "new_users": new_users,
            "cached_page_stats": get_page_stats(7),
        }

        return jsonify(data), 200
    except Exception as e:
        logger.error(f"❌ Analytics summary endpoint failed: {e}")
        return jsonify({"error": str(e)}), 500


# ======================================================
# 🧹 CACHE CLEAR ENDPOINT
# ======================================================
@bp.route("/api/cache/clear", methods=["POST"])
@login_required
def clear_cache():
    """Clears Redis analytics cache."""
    if current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    try:
        keys = redis_client.keys("page_stats:*")
        for k in keys:
            redis_client.delete(k)
        logger.info("🧹 Cleared analytics cache.")
        return jsonify({"status": "cache_cleared", "deleted_keys": len(keys)}), 200
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        return jsonify({"error": str(e)}), 500
