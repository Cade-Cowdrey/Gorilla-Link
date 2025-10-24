from __future__ import annotations
import os, time, json, math, re
from typing import Any, Dict
from flask import Blueprint, jsonify, request

# Import the advanced AI endpoints blueprint from ai_routes.py
# Ensure your project path is: blueprints/api/ai_routes.py
from .ai_routes import ai_bp  # exposed for app registration

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ----------------------
# Utils (safe identity)
# ----------------------
def identity_from_request() -> str:
    ip = request.headers.get("X-Forwarded-For") or request.remote_addr or "unknown"
    ua = request.headers.get("User-Agent", "")[:60]
    return f"ip:{ip}|ua:{ua}"

def ok(data: Any, **meta):
    return jsonify({"ok": True, "data": data, "meta": meta}), 200

def fail(message: str, code: int = 400, **meta):
    return jsonify({"ok": False, "error": {"message": message, "code": code}, "meta": meta}), code

# ----------------------
# Health & Config
# ----------------------
@api_bp.route("/health")
def health():
    return ok({
        "service": "PittState-Connect API",
        "env": os.getenv("FLASK_ENV", "production"),
        "version": os.getenv("APP_VERSION", "v1-final"),
        "time": int(time.time()),
    })

@api_bp.route("/config")
def public_config():
    # Expose safe, non-secret config to the client as needed
    return ok({
        "brand": "PittState Connect",
        "features": {
            "ai_insight_bar": True,
            "ai_helper_panel": True,
            "essay_analyzer": True,
            "resume_optimizer": True,
            "mentor_match_2": True,
        }
    })

# ----------------------
# Lightweight Stats (mock-ready, replace with DB later)
# ----------------------
@api_bp.route("/stats")
def stats():
    # Example aggregate. Replace with real DB queries as needed.
    return ok({
        "users": 4210,
        "posts": 18234,
        "mentors": 128,
        "jobs": 456,
        "updated_at": int(time.time())
    })

# ----------------------
# Analytics (trend stub — separate from AI sentiment trend)
# ----------------------
@api_bp.route("/analytics/engagement")
def analytics_engagement():
    # basic engagement line (fake demo numbers)
    days = int(request.args.get("days", 7))
    data = [{"day": i, "active": int(2600 + 400 * math.sin(i)), "posts": int(300 + 60 * math.cos(i))} for i in range(1, days+1)]
    return ok({"series": data})

# ----------------------
# Moderation passthrough (client may call /api/ai/moderate directly too)
# Provided here if you want a unified entry like /api/security/moderate
# ----------------------
@api_bp.route("/security/moderate", methods=["POST"])
def security_moderate():
    # Forward to AI moderation or run a local heuristic
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return fail("Missing 'text'.", 422)
    # simple heuristic
    bad_words = ["hate", "stupid", "idiot", "kill", "dumb", "trash", "screw you"]
    score = min(1.0, sum(text.lower().count(w) for w in bad_words) * 0.25)
    return ok({"flagged": score >= float(data.get("threshold", 0.8)), "score": round(score, 2)})

# ----------------------
# Donor mini-analytics (non-AI)
# ----------------------
@api_bp.route("/donor/summary")
def donor_summary():
    # Replace with real DB summaries
    resp = {
        "funds": 12,
        "donations_this_term": 384,
        "avg_gift": 142.75,
        "top_fund": "Crimson Legacy",
        "impact_examples": [
            "12 engineering internships supported",
            "8 first-gen scholarships awarded",
            "3 new lab upgrades completed"
        ]
    }
    return ok(resp)

# NOTE:
# - In app_pro.py you should:
#     from blueprints.api.routes import api_bp
#     from blueprints.api.ai_routes import ai_bp
#     app.register_blueprint(api_bp)
#     app.register_blueprint(ai_bp)
#
# - Keeping AI in its own blueprint (`ai_bp`) avoids circular imports and keeps responsibilities clean.
