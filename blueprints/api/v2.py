# blueprints/api/v2.py
from __future__ import annotations
from flask import Blueprint, jsonify, request, current_app
from utils.audit import audit

api_v2_bp = Blueprint("api_v2_bp", __name__, url_prefix="/api/v2")

def _limiter():
    return current_app.extensions["limiter"]

@api_v2_bp.get("/exec/kpis")
@_limiter().limit("60/minute")
def exec_kpis():
    data = {
        "active_users": 1287,
        "scholarships": 52,
        "applications": 231,
        "job_postings": 88,
    }
    return jsonify(data)

@api_v2_bp.get("/employer/postings")
@_limiter().limit("120/minute")
def employer_postings():
    employer_id = request.args.get("employer_id")
    rows = [{"id": 1, "title": "Software Intern", "apps": 14}]
    audit("read", "employer_postings", entity_id=employer_id, meta={"count": len(rows)})
    return jsonify({"postings": rows})
