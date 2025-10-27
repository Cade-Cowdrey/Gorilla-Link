from flask import Blueprint, jsonify, request
from utils.analytics_util import record_api_usage
from utils.mail_util import send_system_alert
from extensions import limiter

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/ping")
@limiter.limit("10/minute")
def ping():
    record_api_usage("/api/ping", "GET")
    return jsonify({"status": "alive", "message": "🦍 PittState-Connect API online"})

@bp.route("/alert", methods=["POST"])
@limiter.limit("5/minute")
def alert():
    data = request.get_json() or {}
    send_system_alert("API Alert", str(data))
    record_api_usage("/api/alert", "POST")
    return jsonify({"sent": True})
