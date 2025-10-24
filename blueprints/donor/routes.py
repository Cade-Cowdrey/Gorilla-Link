# blueprints/donor/routes.py
from __future__ import annotations
from flask import Blueprint, render_template, jsonify

donor_bp = Blueprint("donor_bp", __name__, url_prefix="/donor")

@donor_bp.route("/")
def donor_home():
    # Replace with real DB reads
    model = {
        "funds": 12, "donations_this_term": 384, "avg_gift": 142.75,
        "impact": ["12 engineering internships", "8 first-gen scholarships", "3 lab upgrades"]
    }
    return render_template("donor/overview.html", model=model)

@donor_bp.route("/stats.json")
def donor_stats_json():
    return jsonify(ok=True, data={"funds":12, "donations":384, "avg":142.75})
