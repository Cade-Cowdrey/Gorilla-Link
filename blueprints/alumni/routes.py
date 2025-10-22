# ============================================================
# FILE: blueprints/alumni/routes.py
# ============================================================
from flask import render_template, request
from . import alumni_bp

@alumni_bp.route("/directory", methods=["GET"])
def directory():
    q = request.args.get("q", "")
    alumni = [
        {"name": "Taylor R.", "class_year": 2018, "title": "Data Analyst"},
        {"name": "Sam K.", "class_year": 2016, "title": "Project Engineer"},
    ]
    return render_template("alumni/directory.html", q=q, alumni=alumni)
