from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
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
@system_bp.route("/system/campus/<int:id>/settings", methods=["GET", "POST"])
@login_required
def campus_settings(id):
    """Full campus settings page with configuration options"""
    from flask import render_template, request, flash, redirect, url_for
    from flask_login import current_user
    from models import User
    from models_extended import CampusSettings
    from extensions import db
    
    # Check admin privileges
    if not current_user.is_authenticated or current_user.role.name not in ['admin', 'faculty']:
        flash("Unauthorized access", "danger")
        return redirect(url_for('core_bp.index'))
    
    # Get or create campus settings
    campus = CampusSettings.query.get(id)
    if not campus:
        campus = CampusSettings(
            id=id,
            name="Pittsburg State University",
            code="PSU",
            timezone="America/Chicago",
            settings={}
        )
        db.session.add(campus)
        db.session.commit()
    
    if request.method == "POST":
        try:
            # Update campus settings
            campus.name = request.form.get("name", campus.name)
            campus.code = request.form.get("code", campus.code)
            campus.timezone = request.form.get("timezone", campus.timezone)
            campus.primary_color = request.form.get("primary_color", "#A51C30")
            campus.secondary_color = request.form.get("secondary_color", "#FFC82E")
            
            # Feature toggles
            settings = campus.settings or {}
            settings['enable_mentorship'] = request.form.get("enable_mentorship") == "on"
            settings['enable_job_board'] = request.form.get("enable_job_board") == "on"
            settings['enable_scholarships'] = request.form.get("enable_scholarships") == "on"
            settings['enable_alumni_network'] = request.form.get("enable_alumni_network") == "on"
            settings['enable_events'] = request.form.get("enable_events") == "on"
            settings['enable_ai_tools'] = request.form.get("enable_ai_tools") == "on"
            
            # Notification settings
            settings['notification_email'] = request.form.get("notification_email", "")
            settings['weekly_digest'] = request.form.get("weekly_digest") == "on"
            settings['daily_reports'] = request.form.get("daily_reports") == "on"
            
            # API integrations
            settings['canvas_enabled'] = request.form.get("canvas_enabled") == "on"
            settings['canvas_api_key'] = request.form.get("canvas_api_key", "")
            settings['linkedin_sync'] = request.form.get("linkedin_sync") == "on"
            
            campus.settings = settings
            campus.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash("Campus settings updated successfully!", "success")
            return redirect(url_for('system_bp.campus_settings', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}", "danger")
    
    return render_template("system/campus_settings.html", campus=campus, title=f"Settings - {campus.name}")
