# ============================================================
# FILE: blueprints/scholarships/routes.py
# ============================================================
import os
from flask import render_template, request, redirect, url_for, flash
from . import scholarships_bp

@scholarships_bp.route("/", methods=["GET"])
def index():
    return render_template("scholarships/index.html")

@scholarships_bp.route("/smart-match", methods=["GET"])
def smart_match():
    # Placeholder matches; replace with AI/DB integration when ready
    matches = [
        {"title": "Engineering Leaders Award", "match_score": 92, "tags": ["engineering", "leadership", "junior"]},
        {"title": "First-Gen Scholars Fund", "match_score": 88, "tags": ["first-gen", "any-major"]},
    ]
    return render_template("scholarships/smart_match.html", matches=matches)

@scholarships_bp.route("/essay-helper", methods=["GET", "POST"])
def essay_helper():
    suggestions = None
    if request.method == "POST":
        prompt = (request.form.get("prompt") or "").strip()
        if not prompt:
            flash("Please paste a prompt or draft.", "warning")
            return redirect(url_for("scholarships_bp.essay_helper"))
        # Optional AI stub — gated by env
        if os.getenv("OPENAI_API_KEY"):
            # TODO: call your AI helper; for now, placeholder
            suggestions = "• Tighten your intro.\n• Add an impact example.\n• Close with PSU alignment."
        else:
            suggestions = "AI disabled. Add OPENAI_API_KEY in environment to enable live suggestions."
    return render_template("scholarships/essay_helper.html", suggestions=suggestions)
