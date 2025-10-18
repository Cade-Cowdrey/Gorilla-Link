from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Post, Department, User
from datetime import datetime

careers = Blueprint("careers", __name__, template_folder="templates")

# ----------------------------------------
# 🌍 PUBLIC CAREER LISTINGS
# ----------------------------------------
@careers.route("/careers")
def careers_public():
    """Displays all career, internship, and alumni opportunity posts."""
    departments = Department.query.order_by(Department.name.asc()).all()
    jobs = (
        Post.query.filter_by(category="career")
        .order_by(Post.created_at.desc())
        .limit(15)
        .all()
    )

    return render_template(
        "core/careers.html",
        departments=departments,
        jobs=jobs,
    )


# ----------------------------------------
# 🏛️ DEPARTMENT-SPECIFIC CAREERS
# ----------------------------------------
@careers.route("/careers/department/<int:dept_id>")
def careers_by_department(dept_id):
    """Displays career opportunities filtered by department."""
    department = Department.query.get_or_404(dept_id)
    jobs = (
        Post.query.filter_by(category="career", department_id=dept_id)
        .order_by(Post.created_at.desc())
        .all()
    )

    return render_template(
        "careers/by_department.html",
        department=department,
        jobs=jobs,
    )


# ----------------------------------------
# 🧭 CAREER DETAIL PAGE
# ----------------------------------------
@careers.route("/careers/<int:career_id>")
def career_detail(career_id):
    """Detailed page for a specific job or internship post."""
    career = Post.query.get_or_404(career_id)
    author = User.query.get(career.user_id)
    department = Department.query.get(career.department_id) if career.department_id else None

    return render_template(
        "careers/detail.html",
        career=career,
        author=author,
        department=department,
    )


# ----------------------------------------
# 🧠 ADMIN & FACULTY CAREER DASHBOARD
# ----------------------------------------
@careers.route("/careers/dashboard")
@login_required
def careers_dashboard():
    """Admin or faculty dashboard for managing PSU job posts."""
    if not getattr(current_user, "is_admin", False) and current_user.role not in ["faculty", "staff"]:
        flash("Admin or faculty access required.", "warning")
        return redirect(url_for("careers.careers_public"))

    total_jobs = Post.query.filter_by(category="career").count()
    recent_jobs = (
        Post.query.filter_by(category="career")
        .order_by(Post.created_at.desc())
        .limit(10)
        .all()
    )

    departments = Department.query.all()
    total_departments = len(departments)

    return render_template(
        "careers/dashboard.html",
        total_jobs=total_jobs,
        total_departments=total_departments,
        recent_jobs=recent_jobs,
        departments=departments,
    )


# ----------------------------------------
# 🆕 CREATE NEW CAREER POST
# ----------------------------------------
@careers.route("/careers/create", methods=["GET", "POST"])
@login_required
def create_career():
    """Allows admins or faculty to post a new career opportunity."""
    if not getattr(current_user, "is_admin", False) and current_user.role not in ["faculty", "staff"]:
        flash("Only admins or faculty can create job posts.", "danger")
        return redirect(url_for("careers.careers_public"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        department_id = request.form.get("department_id")
        location = request.form.get("location")
        link = request.form.get("link")

        if not title or not description:
            flash("Title and description are required.", "warning")
            return redirect(url_for("careers.create_career"))

        new_job = Post(
            title=title,
            description=description,
            category="career",
            department_id=department_id if department_id else None,
            location=location,
            link=link,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_job)
        db.session.commit()

        flash(f"Career post '{title}' created successfully!", "success")
        return redirect(url_for("careers.careers_dashboard"))

    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template("careers/create.html", departments=departments)


# ----------------------------------------
# ✏️ EDIT CAREER POST
# ----------------------------------------
@careers.route("/careers/edit/<int:career_id>", methods=["GET", "POST"])
@login_required
def edit_career(career_id):
    """Edit an existing job/internship post."""
    career = Post.query.get_or_404(career_id)

    if not getattr(current_user, "is_admin", False) and current_user.id != career.user_id:
        flash("You do not have permission to edit this post.", "danger")
        return redirect(url_for("careers.careers_dashboard"))

    if request.method == "POST":
        career.title = request.form.get("title")
        career.description = request.form.get("description")
        career.location = request.form.get("location")
        career.link = request.form.get("link")
        career.department_id = request.form.get("department_id")
        db.session.commit()

        flash(f"Career post '{career.title}' updated successfully!", "success")
        return redirect(url_for("careers.careers_dashboard"))

    departments = Department.query.all()
    return render_template("careers/edit.html", career=career, departments=departments)


# ----------------------------------------
# 🗑️ DELETE CAREER POST
# ----------------------------------------
@careers.route("/careers/delete/<int:career_id>", methods=["POST"])
@login_required
def delete_career(career_id):
    """Allows admins or authors to delete a career post."""
    career = Post.query.get_or_404(career_id)

    if not getattr(current_user, "is_admin", False) and current_user.id != career.user_id:
        flash("You do not have permission to delete this post.", "danger")
        return redirect(url_for("careers.careers_dashboard"))

    db.session.delete(career)
    db.session.commit()

    flash(f"Career post '{career.title}' deleted successfully.", "info")
    return redirect(url_for("careers.careers_dashboard"))


# ----------------------------------------
# 📊 CAREER ANALYTICS JSON
# ----------------------------------------
@careers.route("/careers/data")
@login_required
def careers_data():
    """Provides JSON stats for career dashboard charts."""
    total_jobs = Post.query.filter_by(category="career").count()
    by_department = (
        db.session.query(Department.name, db.func.count(Post.id))
        .outerjoin(Post, Department.id == Post.department_id)
        .filter(Post.category == "career")
        .group_by(Department.name)
        .all()
    )

    data = [{"department": d, "job_count": c} for d, c in by_department]
    return jsonify({"total": total_jobs, "by_department": data})


# ----------------------------------------
# 🚀 ROOT REDIRECT
# ----------------------------------------
@careers.route("/")
def careers_root_redirect():
    """Redirect /careers/ base route to public listings."""
    return redirect(url_for("careers.careers_public"))
