# File: blueprints/analytics/routes.py
from __future__ import annotations
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from utils.analytics_util import (
    track_page_view,
    get_page_stats,
    get_top_pages,
    get_timeseries,
)

bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="analytics")

@bp.get("/")
@login_required
def index():
    track_page_view("analytics_dashboard")
    return render_template(
        "analytics/index.html",
        title="Analytics | PittState-Connect",
        user=current_user,
    )

# --- JSON APIs feeding the dashboard ----
@bp.get("/api/summary")
@login_required
def api_summary():
    track_page_view("analytics_api_summary")
    stats = get_page_stats()
    return jsonify(stats)

@bp.get("/api/top-pages")
@login_required
def api_top_pages():
    limit = int(request.args.get("limit", 10))
    data = get_top_pages(limit=limit)
    return jsonify({"limit": limit, "items": data})

@bp.get("/api/timeseries")
@login_required
def api_timeseries():
    days = int(request.args.get("days", 30))
    series = get_timeseries(days=days)
    return jsonify({"days": days, "series": series})
