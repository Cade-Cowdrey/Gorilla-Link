from flask import Blueprint, jsonify, request
from utils.mail_util import send_system_alert
from utils.analytics_util import record_api_usage
from extensions import limiter

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/ping")
@limiter.limit("10/minute")
def ping():
    record_api_usage("/api/ping", "GET")
    return jsonify({"status": "alive", "message": "🦍 PittState-Connect API running"})

@bp.route("/alert", methods=["POST"])
@limiter.limit("5/minute")
def alert():
    data = request.json or {}
    send_system_alert("Manual Alert", str(data))
    record_api_usage("/api/alert", "POST")
    return jsonify({"sent": True})
