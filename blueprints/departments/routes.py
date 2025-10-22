# ============================================================
# FILE: blueprints/departments/routes.py
# ============================================================
from flask import render_template
from . import departments_bp

@departments_bp.route("/", methods=["GET"])
def index():
    depts = [
        {"slug": "technology", "name": "Technology & Workforce Learning"},
        {"slug": "business", "name": "Kelce College of Business"},
        {"slug": "education", "name": "Education"},
        {"slug": "arts-sciences", "name": "Arts & Sciences"},
    ]
    return render_template("departments/index.html", departments=depts)

@departments_bp.route("/<slug>", methods=["GET"])
def detail(slug):
    # TODO: DB lookup by slug
    dept = {"slug": slug, "name": slug.replace("-", " ").title(), "about": "Department overview placeholder."}
    return render_template("departments/detail.html", dept=dept)
