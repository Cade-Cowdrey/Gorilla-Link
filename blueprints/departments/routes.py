from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Department, User, Post, Event
from datetime import datetime

departments = Blueprint("departments", __name__, template_folder="templates")

# ----------------------------------------
# 🧭 PUBLIC DEPARTMENT LISTING
# ----------------------------------------
@departments.route("/departments")
def list_departments():
    """Public list of all PSU departments with basic stats."""
    all_departments = Department.query.order_by(Department.name.asc()).all()

    dept_data = []
    for dept in all_departments:
        member_count = len(dept.users) if hasattr(dept, "users") else 0
        post_count = Post.query.filter_by(department_id=dept.id).count()
        event_count = Event.query.filter_by(department_id=dept.id).count()
        dept_data.append({
            "id": dept.id,
            "name": dept.name,
            "description": getattr(dept, "description", ""),
            "member_count": member_count,
            "post_count": post_count,
            "event_count": event_count
        })

    return render_template("departments/list.html", departments=dept_data)


# ----------------------------------------
# 🧠 DEPARTMENT DETAIL PAGE
# ----------------------------------------
@departments.route("/departments/<int:dept_id>")
def department_detail(dept_id):
    """Detailed department view with members, posts, and events."""
    dept = Department.query.get_or_404(dept_id)
    faculty = User.query.filter_by(department_id=dept.id, role="faculty").all()
    students = User.query.filter_by(department_id=dept.id, role="student").limit(10).all()
    posts = Post.query.filter_by(department_id=dept.id).order_by(Post.created_at.desc()).limit(8).all()
    events = Event.query.filter_by(department_id=dept.id).order_by(Event.start_date.desc()).limit(5).all()

    return render_template(
        "departments/detail.html",
        department=dept,
        faculty=faculty,
        students=students,
        posts=posts,
        events=events,
    )


# ----------------------------------------
# 📊 DEPARTMENT ANALYTICS DASHBOARD
# ----------------------------------------
@departments.route("/departments/dashboard")
@login_required
def departments_dashboard():
    """Analytics dashboard summarizing departmental activity for admins."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "warning")
        return redirect(url_for("core.home"))

    departments_all = Department.query.all()
    data = []
    for d in departments_all:
        user_count = len(d.users) if hasattr(d, "users") else 0
        post_count = Post.query.filter_by(department_id=d.id).count()
        event_count = Event.query.filter_by(department_id=d.id).count()
        data.append({
            "department": d.name,
            "users": user_count,
            "posts": post_count,
            "events": event_count
        })

    totals = {
        "departments": len(departments_all),
        "users": User.query.count(),
        "posts": Post.query.count(),
        "events": Event.query.count()
    }

    return render_template(
        "departments/dashboard.html",
        department_data=data,
        totals=totals
    )


# ----------------------------------------
# 🧮 JSON DATA FOR DEPARTMENT STATS
# ----------------------------------------
@departments.route("/departments/data")
@login_required
def departments_data():
    """JSON endpoint for department analytics charts."""
    data = []
    for dept in Department.query.all():
        user_count = len(dept.users) if hasattr(dept, "users") else 0
        post_count = Post.query.filter_by(department_id=dept.id).count()
        event_count = Event.query.filter_by(department_id=dept.id).count()
        data.append({
            "name": dept.name,
            "users": user_count,
            "posts": post_count,
            "events": event_count,
        })
    return jsonify(data)


# ----------------------------------------
# 🛠️ ADMIN: ADD OR EDIT DEPARTMENTS
# ----------------------------------------
@departments.route("/departments/manage", methods=["GET", "POST"])
@login_required
def manage_departments():
    """Admin or faculty management panel for departments."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "warning")
        return redirect(url_for("core.home"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        if not name:
            flash("Department name cannot be empty.", "warning")
            return redirect(url_for("departments.manage_departments"))

        existing = Department.query.filter_by(name=name).first()
        if existing:
            flash("That department already exists.", "info")
            return redirect(url_for("departments.manage_departments"))

        new_dept = Department(name=name, description=description)
        db.session.add(new_dept)
        db.session.commit()
        flash(f"Department '{name}' created successfully!", "success")
        return redirect(url_for("departments.manage_departments"))

    departments_all = Department.query.order_by(Department.name.asc()).all()
    return render_template("departments/manage.html", departments=departments_all)


# ----------------------------------------
# 🗑️ DELETE A DEPARTMENT
# ----------------------------------------
@departments.route("/departments/delete/<int:dept_id>", methods=["POST"])
@login_required
def delete_department(dept_id):
    """Deletes a department entry (admin only)."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("core.home"))

    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash(f"Department '{dept.name}' deleted successfully.", "info")
    return redirect(url_for("departments.manage_departments"))
