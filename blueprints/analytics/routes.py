# blueprints/analytics/routes.py
from __future__ import annotations

from flask import Blueprint, current_app, render_template, jsonify
from flask_caching import Cache

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

@analytics_bp.get("/")
def index():
    # server-rendered page with a tiny inline card + chart image
    svc = current_app.analytics
    summary = svc.get_summary()
    chart_url = "/api/v1/analytics/chart.png"
    return render_template("analytics/index.html", summary=summary, chart_url=chart_url)

@analytics_bp.get("/summary.json")
def summary_json():
    svc = current_app.analytics
    return jsonify(svc.get_summary())
