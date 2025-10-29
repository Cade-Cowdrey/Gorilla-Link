from flask import Blueprint, jsonify, request
from flask_login import current_user
from utils.analytics_util import record_api_usage
from loguru import logger
from datetime import datetime

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ==========================================================
# 🧠 GENERIC API USAGE TRACKER
# ==========================================================

@api_bp.after_request
def log_api_usage(response):
    """
    Automatically logs API endpoint hits for analytics.
    """
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
# 🔹 EXAMPLE PUBLIC ENDPOINTS
# ==========================================================

@api_bp.route("/status")
def api_status():
    """
    Basic heartbeat for public API access.
    """
    return jsonify({
        "status": "ok",
        "service": "PittState-Connect API",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@api_bp.route("/info")
def api_info():
    """
    Basic system info endpoint.
    """
    info = {
        "app": "PittState-Connect",
        "version": "1.0.0",
        "description": "PSU network and analytics ecosystem.",
        "docs": "https://pittstate-connect.onrender.com/docs",
    }
    return jsonify(info)


# ==========================================================
# 🔒 AUTHENTICATED API EXAMPLE (optional enhancement)
# ==========================================================

@api_bp.route("/user/profile")
def user_profile_api():
    """
    Returns minimal user info if logged in.
    """
    if current_user.is_authenticated:
        return jsonify({
            "id": current_user.id,
            "name": getattr(current_user, "full_name", None),
            "email": getattr(current_user, "email", None),
            "role": getattr(current_user, "role", "student")
        })
    return jsonify({"error": "Unauthorized"}), 401
