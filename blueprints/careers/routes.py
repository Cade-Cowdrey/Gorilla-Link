# ============================================================
# FILE: blueprints/careers/routes.py
# ============================================================
from flask import render_template, request
from . import careers_bp

@careers_bp.route("/", methods=["GET"])
def dashboard():
    # Placeholder data; wire to jobs API/DB later
    filters = {"q": request.args.get("q", ""), "dept": request.args.get("dept")}
    jobs = [
        {"title": "Software Engineering Intern", "company": "Garmin", "location": "Olathe, KS"},
        {"title": "Marketing Analyst", "company": "Honeywell", "location": "KC Metro"},
    ]
    return render_template("careers/dashboard.html", filters=filters, jobs=jobs)
