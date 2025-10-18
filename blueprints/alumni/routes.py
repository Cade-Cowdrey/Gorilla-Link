from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import User, Post, Department, Event
from datetime import datetime

alumni = Blueprint("alumni", __name__, template_folder="templates")

# ----------------------------------------
# 🌍 PUBLIC ALUMNI DIRECTORY
# ----------------------------------------
@alumni.route("/alumni")
def alumni_directory():
    """Public PSU-branded alumni listing with profile summaries."""
    alumni_users = (
        User.query.filter_by(role="alumni")
        .order_by(User.name.asc())
        .limit(50)
        .all()
    )

    alumni_count = len(alumni_users)
    departments = Department.query.all()

    return render_template(
        "alumni/directory.html",
        alumni_users=alumni_users,
        alumni_count=alumni_count,
        departments=departments,
    )


# ----------------------------------------
# 🧠 ALUMNI PROFILE PAGE
# ----------------------------------------
@alumni.route("/alumni/<int:user_id>")
def alumni_profile(user_id):
    """Detailed profile page for an individual alumnus."""
    alumnus = User.query.get_or_404(user_id)
    if alumnus.role != "alumni":
        flash("This profile is not an alumni record.", "warning")
        return redirect(url_for("alumni.alumni_directory"))

    posts = Post.query.filter_by(user_id=alumnus.id).order_by(Post.created_at.desc()).limit(5).all()
    department = Department.query.get(alumnus.department_id) if alumnus.department_id else None

    return render_template(
        "alumni/details.html",
        alumnus=alumnus,
        posts=posts,
        department=department,
    )


# ----------------------------------------
# 🧭 ALUMNI DASHBOARD (ADMIN / STAFF)
# ----------------------------------------
@alumni.route("/alumni/dashboard")
@login_required
def alumni_dashboard():
    """Admin or staff view of alumni statistics and activity."""
    if not getattr(current_user, "is_admin", False) and current_user.role not in ["staff", "faculty"]:
        flash("Admin or staff access required.", "warning")
        return redirect(url_for("alumni.alumni_directory"))

    total_alumni = User.query.filter_by(role="alumni").count()
    recent_alumni = (
        User.query.filter_by(role="alumni")
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )
    total_departments = Department.query.count()
    alumni_by_department = (
        db.session.query(Department.name, db.func.count(User.id))
        .outerjoin(User, Department.id == User.department_id)
        .filter(User.role == "alumni")
        .group_by(Department.name)
        .all()
    )

    data = [{"department": d, "count": c} for d, c in alumni_by_department]

    return render_template(
        "alumni/dashboard.html",
        total_alumni=total_alumni,
        total_departments=total_departments,
        recent_alumni=recent_alumni,
        alumni_data=data,
    )


# ----------------------------------------
# 🤝 MENTORSHIP MATCHING
# ----------------------------------------
@alumni.route("/alumni/mentorship")
@login_required
def mentorship_portal():
    """Mentorship page connecting students with alumni mentors."""
    students = User.query.filter_by(role="student").limit(10).all()
    alumni_users = User.query.filter_by(role="alumni").limit(10).all()

    return render_template(
        "alumni/mentorship.html",
        students=students,
        alumni_users=alumni_users,
    )


@alumni.route("/alumni/mentorship/match", methods=["POST"])
@login_required
def mentorship_match():
    """Creates a mentorship match record (demo simulation)."""
    student_id = request.form.get("student_id")
    alumni_id = request.form.get("alumni_id")

    if not student_id or not alumni_id:
        flash("Both student and alumni selections are required.", "warning")
        return redirect(url_for("alumni.mentorship_portal"))

    student = User.query.get(student_id)
    mentor = User.query.get(alumni_id)
    if not student or not mentor:
        flash("Invalid match data.", "danger")
        return redirect(url_for("alumni.mentorship_portal"))

    flash(f"{student.name} has been matched with mentor {mentor.name}!", "success")
    return redirect(url_for("alumni.mentorship_portal"))


# ----------------------------------------
# 🗂️ ALUMNI EVENTS & NETWORKING
# ----------------------------------------
@alumni.route("/alumni/events")
def alumni_events():
    """Displays PSU events specifically for alumni networking."""
    events = (
        Event.query.filter(Event.title.ilike("%alumni%"))
        .order_by(Event.start_date.desc())
        .limit(10)
        .all()
    )
    return render_template("alumni/events.html", events=events)


# ----------------------------------------
# 📊 ALUMNI ANALYTICS DATA
# ----------------------------------------
@alumni.route("/alumni/data")
@login_required
def alumni_data():
    """Provides JSON data for alumni statistics and charts."""
    total_alumni = User.query.filter_by(role="alumni").count()
    alumni_by_department = (
        db.session.query(Department.name, db.func.count(User.id))
        .outerjoin(User, Department.id == User.department_id)
        .filter(User.role == "alumni")
        .group_by(Department.name)
        .all()
    )

    data = [{"department": d, "count": c} for d, c in alumni_by_department]
    return jsonify({"total": total_alumni, "by_department": data})


# ----------------------------------------
# 🧭 ROOT REDIRECT
# ----------------------------------------
@alumni.route("/")
def alumni_root_redirect():
    """Redirect /alumni/ base path to directory."""
    return redirect(url_for("alumni.alumni_directory"))
