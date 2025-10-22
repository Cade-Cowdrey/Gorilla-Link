# ============================================================
# FILE: blueprints/mentors/routes.py
# ============================================================
from flask import render_template, request
from . import mentors_bp

@mentors_bp.route("/", methods=["GET"])
def hub():
    q = request.args.get("q", "")
    mentors = [
        {"name": "Jordan A.", "dept": "Technology", "sessions": 12},
        {"name": "Maria L.", "dept": "Business", "sessions": 9},
        {"name": "Chris M.", "dept": "Education", "sessions": 8},
    ]
    return render_template("mentors/hub.html", mentors=mentors, q=q)
