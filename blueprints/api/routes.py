from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from utils.analytics_util import run_usage_analytics
from openai import OpenAI
from redis import Redis
import os, json

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ------------------------------------------------------
# Cached Metrics (using Redis if available)
# ------------------------------------------------------
def get_cached_metrics():
    """Attempt to retrieve analytics data from Redis cache."""
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return None
        r = Redis.from_url(redis_url)
        cached = r.get("pittstate_connect:analytics_latest")
        if cached:
            return json.loads(cached)
    except Exception as e:
        current_app.logger.warning(f"[API] Redis cache unavailable: {e}")
    return None

def set_cached_metrics(data):
    """Store analytics snapshot in Redis for 1 hour."""
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return
        r = Redis.from_url(redis_url)
        r.setex("pittstate_connect:analytics_latest", 3600, json.dumps(data))
    except Exception as e:
        current_app.logger.warning(f"[API] Failed to set Redis cache: {e}")


# ------------------------------------------------------
# Analytics Endpoint
# ------------------------------------------------------
@api_bp.route("/analytics/latest")
def analytics_latest():
    """Return most recent analytics snapshot."""
    from app_pro import db

    # Check Redis cache first
    data = get_cached_metrics()
    if data:
        data["source"] = "cache"
        current_app.logger.info("[API] Served analytics from cache.")
        return jsonify(data)

    # Fallback: recalc metrics
    try:
        data = run_usage_analytics(db)
        data["source"] = "live"
        set_cached_metrics(data)
        current_app.logger.info("[API] Served analytics (fresh calculation).")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"[API] Analytics generation failed: {e}")
        return jsonify({"error": "Failed to retrieve analytics"}), 500


# ------------------------------------------------------
# AI Insight Endpoint
# ------------------------------------------------------
@api_bp.route("/ai/insight", methods=["POST"])
def ai_insight():
    """
    Generate a quick AI-based summary or interpretation of analytics data.
    Connects to OpenAI for narrative summaries and PSU-style insights.
    """
    prompt = request.json.get("prompt", "")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"insight": "AI API key missing or invalid."}), 500

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the PSU Analytics Assistant for PittState-Connect. "
                        "Use a positive, analytical tone. Be concise, data-driven, and encouraging."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=80,
        )
        text = completion.choices[0].message.content.strip()
        return jsonify({
            "insight": text,
            "generated_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        current_app.logger.warning(f"[API] AI insight generation failed: {e}")
        return jsonify({
            "insight": "Insight unavailable at this time.",
            "error": str(e)
        }), 500


# ------------------------------------------------------
# AI Utility Endpoint (Optional Power-up)
# ------------------------------------------------------
@api_bp.route("/ai/health")
def ai_health():
    """Lightweight OpenAI connectivity test."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        models = client.models.list()
        return jsonify({
            "status": "ok",
            "models_available": len(models.data),
            "checked_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ------------------------------------------------------
# System Health Endpoint
# ------------------------------------------------------
@api_bp.route("/system/health")
def system_health():
    """Health endpoint for monitoring uptime and integrations."""
    status = {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    try:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            r = Redis.from_url(redis_url)
            r.ping()
            status["redis"] = "connected"
        else:
            status["redis"] = "disabled"
    except Exception:
        status["redis"] = "unavailable"

    try:
        from app_pro import db
        db.session.execute("SELECT 1")
        status["database"] = "connected"
    except Exception:
        status["database"] = "unavailable"

    return jsonify(status)
