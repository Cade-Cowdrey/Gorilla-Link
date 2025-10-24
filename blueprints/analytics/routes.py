from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

# ======================================================
# PSU Analytics Dashboard — Gorilla Data Insights
# ======================================================
@analytics_bp.route("/dashboard")
@login_required
def dashboard():
    # Sample analytics data, normally fetched from db/cache
    stats = {
        "logins_today": 42,
        "active_users": 128,
        "scholarship_apps": 36,
        "jobs_viewed": 89,
        "messages_sent": 214,
    }
    return render_template("analytics/dashboard.html", stats=stats)

# ======================================================
# API: Analytics Insights JSON
# ======================================================
@analytics_bp.route("/api/insights")
@login_required
def insights():
    now = datetime.utcnow().isoformat()
    data = {
        "timestamp": now,
        "user_id": current_user.id if current_user.is_authenticated else None,
        "session_metrics": {
            "logins_today": 42,
            "new_posts": 17,
            "avg_session_time": "3m 25s",
            "most_active_dept": "Engineering Tech",
        },
    }
    return jsonify(data)

# ======================================================
# AI-Powered Trend Analysis (Optional Enhancement)
# ======================================================
@analytics_bp.route("/ai/trends", methods=["POST"])
@login_required
def ai_trends():
    """Generate analytical summaries via OpenAI if available."""
    text = request.json.get("prompt", "")
    if not text:
        return jsonify({"error": "Missing prompt"}), 400

    client = getattr(current_app, "openai_client", None)
    if not client:
        return jsonify({"error": "AI client unavailable"}), 503

    try:
        completion = client.chat.completions.create(
            model=current_app.config["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are an analytical assistant for PittState-Connect."},
                {"role": "user", "content": text},
            ],
            max_tokens=300,
            temperature=0.5,
        )
        result = completion.choices[0].message.content
        return jsonify({"summary": result})
    except Exception as e:
        current_app.logger.error(f"AI Trends error: {e}")
        return jsonify({"error": "AI generation failed"}), 500
