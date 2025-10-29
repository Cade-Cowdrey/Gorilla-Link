from flask import Blueprint, jsonify, request
from flask_login import current_user
from utils.analytics_util import record_api_usage
from loguru import logger
from datetime import datetime

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ==========================================================
# 🧠 API USAGE LOGGING
# ==========================================================

@api_bp.after_request
def log_api_usage(response):
    try:
        record_api_usage(
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            user_id=current_user.id if current_user.is_authenticated else None,
        )
    except Exception as e:
        logger.warning(f"⚠️ API usage logging failed: {e}")
    return response


# ==========================================================
# 🔹 PUBLIC ENDPOINTS
# ==========================================================

@api_bp.route("/status")
def api_status():
    return jsonify({
        "status": "ok",
        "service": "PittState-Connect API",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@api_bp.route("/info")
def api_info():
    return jsonify({
        "app": "PittState-Connect",
        "version": "1.0.0",
        "description": "PSU network & analytics ecosystem",
        "docs": "/docs"
    })


# ==========================================================
# 🔒 AUTHENTICATED ENDPOINT
# ==========================================================

@api_bp.route("/user/profile")
def user_profile_api():
    if current_user.is_authenticated:
        return jsonify({
            "id": current_user.id,
            "name": getattr(current_user, "full_name", None),
            "email": getattr(current_user, "email", None),
            "role": getattr(current_user, "role", "student"),
        })
    return jsonify({"error": "Unauthorized"}), 401

# 👇 Required for auto-registration
bp = api_bp
