# blueprints/api/routes.py
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.exceptions import BadRequest
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

@api_bp.get("/v1/health")
def api_health():
    return jsonify({"status": "ok"}), 200

@api_bp.get("/v1/info")
def api_info():
    cfg = current_app.config
    return jsonify({
        "name": "PittState-Connect API",
        "version": "1.0.0",
        "env": cfg.get("ENV"),
        "ga_enabled": bool(cfg.get("GOOGLE_ANALYTICS_ID")),
    })

@api_bp.post("/v1/echo")
def api_echo():
    payload = request.get_json(silent=True) or {}
    return jsonify({"you_sent": payload}), 200

@api_bp.get("/v1/analytics/summary")
def api_analytics_summary():
    svc = current_app.analytics
    summary = svc.get_summary()
    return jsonify(summary), 200

@api_bp.get("/v1/analytics/chart.png")
def api_analytics_chart():
    # tiny chart (last 7 days visits)
    svc = current_app.analytics
    points = svc.get_timeseries(days=7)
    days = [p["day"] for p in points]
    visits = [p["visits"] for p in points]

    fig = plt.figure(figsize=(6, 3.2), dpi=140)
    plt.plot(days, visits, marker="o")
    plt.title("Visits (7d)")
    plt.xlabel("Day")
    plt.ylabel("Visits")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")
