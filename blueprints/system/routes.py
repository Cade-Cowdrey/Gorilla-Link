from flask import Blueprint, render_template, jsonify
from datetime import datetime

system_bp = Blueprint("system_bp", __name__, template_folder="../../templates/system")


# ------------------------------------------------------------
#  MULTI-CAMPUS OVERVIEW
# ------------------------------------------------------------
@system_bp.route("/system/multicampus")
def multicampus():
    campuses = [
        {
            "id": 1,
            "name": "Main Campus",
            "location": "Pittsburg, KS",
            "metrics": {
                "active_users": 1020,
                "scholarships_applied": 230,
                "jobs_posted": 88,
                "events_month": 12
            },
        },
        {
            "id": 2,
            "name": "Business College",
            "location": "Kelce Hall",
            "metrics": {
                "active_users": 420,
                "scholarships_applied": 80,
                "jobs_posted": 32,
                "events_month": 6
            },
        },
    ]
    trend_data = {"labels": ["A", "B", "C", "D"], "values": [86, 72, 91, 77]}
    ai_highlights = [
        "Campus A: Scholarship completion ↑ 19%",
        "Campus B: Employer engagement trending ↓ – recommend outreach",
        "Campus C: Event RSVPs breaking records"
    ]
    return render_template(
        "system/multicampus.html",
        campuses=campuses,
        trend_data=trend_data,
        ai_highlights=ai_highlights
    )


# ------------------------------------------------------------
#  CAMPUS DETAIL
# ------------------------------------------------------------
@system_bp.route("/system/campus/<int:id>")
def campus_detail(id):
    sample = {
        "id": id,
        "name": f"Campus {id}",
        "departments": 12,
        "students": 580 + id * 20,
        "faculty": 60 + id * 5,
        "last_update": datetime.utcnow()
    }
    return jsonify(sample)


# ------------------------------------------------------------
#  CAMPUS SETTINGS
# ------------------------------------------------------------
@system_bp.route("/system/campus/<int:id>/settings")
def campus_settings(id):
    return f"Settings page for Campus {id} — coming soon."
