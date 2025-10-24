# blueprints/api/routes.py
# ===============================================================
#  PittState-Connect API Gateway
#  ---------------------------------------------------------------
#  Exposes:
#   • /api/ai/query                → Chat / general AI Q&A
#   • /api/ai/tools/analyze_essay  → Essay feedback helper
#   • /api/ai/tools/optimize_resume→ Résumé optimization helper
#   • /api/ai/moderate             → Content moderation
#   • /api/ai/insight              → Analytics AI insight generation
#   • /api/analytics/summary       → Dashboard data feed
# ===============================================================

from __future__ import annotations
import os, traceback
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from datetime import datetime

# Optional: OpenAI client (works if key is configured)
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ---------------------------------------------------------------
#  Helper Utilities
# ---------------------------------------------------------------
def safe_openai_call(prompt: str, system_prompt: str = "You are a helpful PittState assistant."):
    """Safely call OpenAI if configured, else fallback with generic text."""
    if not client:
        return {"answer": f"[Offline Mode] AI unavailable. (Prompt: {prompt[:100]})"}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return {"answer": response.choices[0].message.content.strip()}
    except Exception as e:
        current_app.logger.error(f"OpenAI Error: {e}")
        return {"answer": f"⚠️ AI request failed. Please try again later."}

def json_error(msg, code=400):
    return jsonify({"success": False, "error": msg}), code


# ---------------------------------------------------------------
#  AI: General Query Endpoint
# ---------------------------------------------------------------
@api_bp.route("/ai/query", methods=["POST"])
def ai_query():
    data = request.get_json() or {}
    q = data.get("q", "").strip()

    if not q:
        return json_error("Missing query prompt.")

    result = safe_openai_call(q)
    return jsonify({"success": True, "data": result, "timestamp": datetime.utcnow().isoformat()})


# ---------------------------------------------------------------
#  AI: Essay Analyzer
# ---------------------------------------------------------------
@api_bp.route("/ai/tools/analyze_essay", methods=["POST"])
def analyze_essay():
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return json_error("Missing essay text.")

    prompt = f"Review this student essay and give clear feedback:\n\n{text}"
    result = safe_openai_call(prompt, system_prompt="You are an academic writing assistant for PittState students.")
    return jsonify({"success": True, "data": result})


# ---------------------------------------------------------------
#  AI: Résumé Optimizer
# ---------------------------------------------------------------
@api_bp.route("/ai/tools/optimize_resume", methods=["POST"])
def optimize_resume():
    data = request.get_json() or {}
    bullets = data.get("bullets", [])

    if not bullets or not isinstance(bullets, list):
        return json_error("Invalid or missing résumé bullet points.")

    prompt = "Optimize the following résumé bullets for clarity, impact, and professionalism:\n" + "\n".join(bullets)
    result = safe_openai_call(prompt, system_prompt="You are a career development advisor for PittState-Connect.")
    return jsonify({"success": True, "data": result})


# ---------------------------------------------------------------
#  AI: Content Moderation
# ---------------------------------------------------------------
@api_bp.route("/ai/moderate", methods=["POST"])
def moderate():
    data = request.get_json() or {}
    text = data.get("text", "")

    if not text:
        return json_error("Missing text for moderation.")

    flags = any(word in text.lower() for word in ["hate", "violence", "racist", "attack", "sexual"])
    response = {
        "flagged": flags,
        "severity": "high" if flags else "none",
        "timestamp": datetime.utcnow().isoformat(),
    }
    return jsonify({"success": True, "data": response})


# ---------------------------------------------------------------
#  AI: Insight / Analytics Summary
# ---------------------------------------------------------------
@api_bp.route("/ai/insight", methods=["POST"])
def ai_insight():
    data = request.get_json() or {}
    context = data.get("context", "Generate a high-level summary of current campus engagement metrics.")

    result = safe_openai_call(context, system_prompt="You are PittState-Connect’s analytics summarizer.")
    return jsonify({"success": True, "data": result})


# ---------------------------------------------------------------
#  Analytics: Summary Data (Dashboard Feed)
# ---------------------------------------------------------------
@api_bp.route("/analytics/summary", methods=["GET"])
def analytics_summary():
    """Provide latest site-level statistics for dashboards."""
    try:
        # These would normally be fetched from your DB or analytics table
        metrics = {
            "users_total": 4521,
            "alumni": 1673,
            "active_sessions": 121,
            "open_scholarships": 38,
            "events_upcoming": 12,
            "jobs_posted": 84,
            "avg_match_score": 87,
        }

        return jsonify({
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        current_app.logger.error(f"Analytics Summary Error: {traceback.format_exc()}")
        return json_error("Unable to retrieve analytics.")


# ---------------------------------------------------------------
#  Global Error Handlers (API-only)
# ---------------------------------------------------------------
@api_bp.app_errorhandler(404)
def not_found(e):
    return json_error("Endpoint not found.", 404)

@api_bp.app_errorhandler(500)
def internal_error(e):
    current_app.logger.error(f"500 Error: {traceback.format_exc()}")
    return json_error("Internal server error.", 500)
