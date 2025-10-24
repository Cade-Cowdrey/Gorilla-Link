"""
PittState-Connect API Blueprint
Advanced PSU-branded REST/AI/Analytics interface.

Endpoints:
  /api/ping               → Health check
  /api/ai/ask             → Chat/AI assistant (OpenAI)
  /api/analytics/summary  → Aggregate analytics data
  /api/reminders/schedule → Smart reminder scheduler
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import traceback
import time

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------
def _json_response(success=True, **data):
    """Standardized PSU API response format."""
    return jsonify({
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": data,
    })


def _error_response(message, code=400, trace=None):
    """Unified error wrapper for client responses."""
    payload = {
        "success": False,
        "error": {"message": message, "code": code},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if trace and current_app.config.get("DEBUG"):
        payload["error"]["trace"] = trace
    return jsonify(payload), code


# ---------------------------------------------------------
# 1️⃣ Health check
# ---------------------------------------------------------
@api_bp.route("/ping", methods=["GET"])
def ping():
    """Simple health endpoint for uptime and latency checks."""
    start = time.perf_counter()
    redis_status = bool(getattr(current_app, "redis_client", None))
    openai_status = bool(current_app.config.get("OPENAI_API_KEY"))
    db_status = False

    try:
        from models import User
        User.query.first()
        db_status = True
    except Exception:
        db_status = False

    latency = round((time.perf_counter() - start) * 1000, 2)
    return _json_response(
        status="ok",
        latency_ms=latency,
        database=db_status,
        redis=redis_status,
        openai=openai_status,
        version="2.0-Final",
    )


# ---------------------------------------------------------
# 2️⃣ AI Assistant Endpoint (OpenAI integration)
# ---------------------------------------------------------
@api_bp.route("/ai/ask", methods=["POST"])
def ai_ask():
    """
    Smart AI endpoint — responds to queries using OpenAI.
    Requires: { "prompt": "..." }
    """
    if not current_app.config.get("OPENAI_API_KEY"):
        return _error_response("OpenAI API not configured.", 503)

    payload = request.get_json(silent=True)
    if not payload or "prompt" not in payload:
        return _error_response("Missing prompt field.", 400)

    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return _error_response("Prompt cannot be empty.", 400)

    try:
        import openai

        openai.api_key = current_app.config["OPENAI_API_KEY"]

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are PittState-Connect's helpful AI assistant, tailored to PSU students, alumni, and staff."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        answer = response.choices[0].message.content.strip()
        return _json_response(prompt=prompt, response=answer)
    except Exception as e:
        return _error_response("AI generation failed.", 500, trace=traceback.format_exc())


# ---------------------------------------------------------
# 3️⃣ Analytics Summary Endpoint
# ---------------------------------------------------------
@api_bp.route("/analytics/summary", methods=["GET"])
def analytics_summary():
    """
    Returns cached or live metrics for dashboard analytics.
    Example return:
    {
      "users_total": 523,
      "active_today": 97,
      "posts_created": 134,
      "scholarships_applied": 43,
      "timestamp": "..."
    }
    """
    try:
        cache = current_app.extensions.get("cache")
        data = cache.get("analytics:summary")

        if not data:
            from models import User, Post, ScholarshipApplication

            total_users = User.query.count()
            posts = Post.query.count() if "Post" in globals() else 0
            scholarships = (
                ScholarshipApplication.query.count()
                if "ScholarshipApplication" in globals()
                else 0
            )

            data = {
                "users_total": total_users,
                "posts_created": posts,
                "scholarships_applied": scholarships,
                "active_today": min(total_users, int(total_users * 0.2)),  # rough sample
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            cache.set("analytics:summary", data, timeout=3600)

        return _json_response(**data)

    except Exception as e:
        return _error_response("Analytics aggregation failed.", 500, trace=traceback.format_exc())


# ---------------------------------------------------------
# 4️⃣ Smart Reminder Scheduler
# ---------------------------------------------------------
@api_bp.route("/reminders/schedule", methods=["POST"])
def schedule_reminder():
    """
    Queue a reminder job via APScheduler or Redis queue.
    Request JSON: { "user_id": 12, "message": "...", "when": "2025-10-26T15:00:00Z" }
    """
    scheduler = getattr(current_app, "scheduler", None)
    if not scheduler:
        return _error_response("Scheduler not available.", 503)

    payload = request.get_json(silent=True)
    if not payload:
        return _error_response("Missing JSON body.", 400)

    try:
        user_id = int(payload.get("user_id"))
        message = payload.get("message", "")
        when_str = payload.get("when")
        when = datetime.fromisoformat(when_str.replace("Z", "")) if when_str else None

        if not all([user_id, message, when]):
            return _error_response("Missing user_id, message, or when.", 400)

        def send_reminder(user_id=user_id, msg=message):
            try:
                from utils.mail_util import send_email
                from models import User

                user = User.query.get(user_id)
                if not user or not user.email:
                    return
                send_email(
                    user.email,
                    "PittState-Connect Reminder",
                    f"<p>{msg}</p><br><small>Sent automatically by PittState-Connect.</small>",
                )
                current_app.logger.info(f"✅ Reminder sent to user {user_id}: {msg}")
            except Exception as e:
                current_app.logger.warning(f"Reminder job failed: {e}")

        job_id = f"reminder_{user_id}_{int(time.time())}"
        scheduler.add_job(
            send_reminder,
            "date",
            run_date=when,
            id=job_id,
            replace_existing=True,
        )

        return _json_response(message="Reminder scheduled successfully.", job_id=job_id, run_date=when.isoformat())

    except Exception as e:
        return _error_response("Failed to schedule reminder.", 500, trace=traceback.format_exc())


# ---------------------------------------------------------
# 5️⃣ Error handler for /api
# ---------------------------------------------------------
@api_bp.errorhandler(404)
def api_not_found(_):
    return _error_response("Endpoint not found.", 404)
