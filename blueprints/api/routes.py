from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
import logging
import re
import datetime
from utils.ai_util import generate_ai_job_insight
from utils.analytics_util import record_api_usage
from utils.mail_util import send_system_alert
from extensions import redis_client

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# =========================================================
# ✅ Smart Match AI Insight Endpoint (production-ready)
# =========================================================
@api_bp.route("/ai-insight", methods=["GET"])
def ai_insight():
    """
    Generate AI-based career insights and job recommendations.
    Features:
      - Input sanitization
      - Redis caching for speed
      - Full logging and analytics tracking
      - Error fallback to maintain uptime
    """
    query = request.args.get("query", "").strip()
    user_email = getattr(current_user, "email", "guest")

    # --- Validate input ---------------------------------------------------
    if not query or len(query) < 3:
        return jsonify({"error": "Please enter a valid search term."}), 400

    safe_query = re.sub(r"[^a-zA-Z0-9\s,]", "", query)

    try:
        # --- Check Redis cache -------------------------------------------
        cache_key = f"ai_insight:{safe_query.lower()}"
        cached_response = redis_client.get(cache_key)
        if cached_response:
            logger.info(f"✅ Cache hit for AI insight: {safe_query}")
            record_api_usage("ai_insight_cached", user_email)
            return jsonify({"insight": cached_response.decode("utf-8"), "cached": True})

        # --- Generate fresh AI insight -----------------------------------
        logger.info(f"🤖 Generating new AI insight for: {safe_query} by {user_email}")
        record_api_usage("ai_insight_request", user_email)

        insight = generate_ai_job_insight(safe_query)

        if not insight:
            insight = "No AI insights are currently available for this query."

        # --- Cache for future reuse --------------------------------------
        redis_client.setex(cache_key, 3600, insight)

        # --- Structured response -----------------------------------------
        return jsonify({
            "insight": insight,
            "cached": False,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        logger.exception(f"❌ AI Insight generation failed: {e}")
        send_system_alert("AI Insight API Failure", str(e))
        return jsonify({"error": "Server temporarily unavailable. Please try again later."}), 500


# =========================================================
# ✅ Job Listings API (public-friendly with analytics)
# =========================================================
@api_bp.route("/jobs", methods=["GET"])
def jobs():
    """
    Public API for all job listings — supports dashboard and department pages.
    """
    from models import Job  # imported here to avoid circular dependency

    try:
        jobs = Job.query.order_by(Job.date_posted.desc()).limit(50).all()
        record_api_usage("api_jobs_list", getattr(current_user, "email", "guest"))

        return jsonify({
            "count": len(jobs),
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "department": j.department.name if j.department else "General",
                    "description": j.description[:250] + "...",
                    "posted": j.date_posted.strftime("%Y-%m-%d")
                } for j in jobs
            ]
        })

    except Exception as e:
        logger.error(f"Error retrieving job list: {e}")
        send_system_alert("API Job List Error", str(e))
        return jsonify({"error": "Could not retrieve jobs"}), 500


# =========================================================
# ✅ Health Check & Meta API
# =========================================================
@api_bp.route("/health")
def health():
    """Simple service health endpoint for uptime monitoring."""
    try:
        redis_ok = redis_client.ping()
        return jsonify({
            "status": "ok",
            "redis": redis_ok,
            "service": "PittState-Connect API",
            "time": datetime.datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        logger.warning(f"⚠️ Health check issue: {e}")
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 503
