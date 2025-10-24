# blueprints/employer/routes.py
from __future__ import annotations
from flask import Blueprint, render_template, jsonify, request

employer_bp = Blueprint("employer_bp", __name__, url_prefix="/employer")

@employer_bp.route("/")
def employer_home():
    model = {
        "openings": [
            {"title":"Software Intern","dept":"Engineering","status":"Open"},
            {"title":"Marketing Assistant","dept":"Business","status":"Open"},
        ],
        "sponsored": 3
    }
    return render_template("employer/overview.html", model=model)

@employer_bp.route("/openings", methods=["POST"])
def add_opening():
    data = request.get_json(silent=True) or {}
    # TODO: persist to DB
    return jsonify(ok=True, data={"received": data})
