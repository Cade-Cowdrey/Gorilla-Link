from flask import Blueprint, render_template, request
from utils.openai_util import ai_scholarship_smart_match, ai_essay_suggestions

scholarships_bp = Blueprint("scholarships_bp", __name__, template_folder="../../templates")

@scholarships_bp.route("/")
def index():
    return render_template("scholarships/index.html")

@scholarships_bp.route("/smart-match")
def smart_match():
    # Demo data
    profile = {"tags": ["engineering", "first-gen", "leadership"]}
    scholarships = [
        {"title": "Engineering Excellence", "tags": ["engineering", "gpa"]},
        {"title": "First-Gen Scholar", "tags": ["first-gen"]},
        {"title": "Leadership Award", "tags": ["leadership", "community"]},
    ]
    matches = ai_scholarship_smart_match(profile, scholarships)
    return render_template("scholarships/smart_match.html", matches=matches)

@scholarships_bp.route("/essay-helper", methods=["GET", "POST"])
def essay_helper():
    suggestions = None
    if request.method == "POST":
        suggestions = ai_essay_suggestions(request.form.get("prompt", ""))
    return render_template("scholarships/essay_helper.html", suggestions=suggestions)
