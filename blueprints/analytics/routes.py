# File: blueprints/analytics/routes.py
from __future__ import annotations

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from utils.analytics_util import record_page_view, get_page_stats, get_top_pages, get_timeseries

# Analytics blueprint using a standard bp variable and _bp suffix name
bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

@bp.get("/health")
def health():
    """Health endpoint for monitoring."""
    return jsonify(status="ok", section="analytics")

@bp.get("/")
@login_required
def index():
    """Render the analytics dashboard page and record a page view."""
    record_page_view("analytics_dashboard", current_user.id if current_user.is_authenticated else None)
    return render_template(
        "analytics/index.html",
        title="Analytics | PittState-Connect",
        user=current_user,
    )

# --- JSON APIs feeding the dashboard ----
@bp.get("/api/summary")
@login_required
def api_summary():
    """Return summary statistics for the analytics dashboard."""
    record_page_view("analytics_api_summary", current_user.id if current_user.is_authenticated else None)
    stats = get_page_stats()

@bp.get("/api/top-pages")
@login_required
def api_top_pages():
    """Return top pages viewed over a period (default limit=10)."""
    record_page_view("analytics_api_top_pages", current_user.id if current_user.is_authenticated else None)
    limit = int(request.args.get("limit", 10))
    data = get_top_pages(limit=limit)
    return jsonify({"limit": limit, "items": data})

@bp.get("/api/timeseries")
@login_required
def api_timeseries():
    """Return a time series of page views for the past N days (default 30 days)."""
    record_page_view("analytics_api_timeseries", current_user.id if current_user.is_authenticated else None)
    days = int(request.args.get("days", 30))
    data = get_timeseries(days=days)
    return jsonify({"days": days, "series": data})

    return jsonify(stats)

@bp.get("/api/top-pages")
@login_required
def api_top_pages():
    """Return top pages viewed over a period (default limit=10)."""
    record_page_view("analytics_api_top_pages", current_user.id if current_user.is_authenticated else None)
    limit = int(request.args.get("limit", 10))
    data = get_top_pages(limit=limit)
    return jsonify({"limit": limit, "items": data})

@bp.get("/api/timeseries")
@login_required
def api_timeseries():
    """Return a time series of page views for the past N days (default 30 days)."""
    record_page_view("analytics_api_timeseries", current_user.id if current_user.is_authenticated else None)
    days = int(request.args.get("days", 30))
    data = get_timeseries(days=days)
    return jsonify({"days": days, "series": data})
