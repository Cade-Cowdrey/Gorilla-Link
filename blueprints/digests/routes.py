# blueprints/digests/routes.py
from __future__ import annotations
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

digests_bp = Blueprint("digests_bp", __name__, url_prefix="/digests")

def _summarize_posts(posts: list[dict]) -> dict:
    """Simple engagement-based post summary."""
    top = sorted(posts, key=lambda p: (p.get("likes", 0) * 2 + p.get("comments", 0)), reverse=True)[:5]
    tags = {}
    for p in top:
        for t in p.get("tags", []):
            tags[t] = tags.get(t, 0) + 1
    return {
        "top_posts": top,
        "top_tags": sorted(tags.items(), key=lambda kv: kv[1], reverse=True)[:5],
        "takeaway": "High engagement around " + (top[0].get("title", "campus topics") if top else "campus life")
    }

@digests_bp.route("/preview", methods=["POST"])
def preview_digest():
    """Preview the auto-generated campus digest (HTML-only)."""
    payload = request.get_json(silent=True) or {}
    posts = payload.get("posts", [])
    jobs = payload.get("jobs", [])
    events = payload.get("events", [])
    summary = _summarize_posts(posts)
    html = render_template("emails/digests/digest.html",
                           date=datetime.utcnow().strftime("%b %d, %Y"),
                           posts=summary["top_posts"], tags=summary["top_tags"],
                           jobs=jobs[:5], events=events[:5], takeaway=summary["takeaway"])
    return jsonify({"ok": True, "html": html, "meta": {"generated_at": int(time.time())}})

@digests_bp.route("/send", methods=["POST"])
def send_digest():
    """Simulated email send endpoint — integrate Flask-Mail or SES here."""
    return preview_digest()
