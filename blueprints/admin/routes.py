# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Admin Blueprint Routes
# ---------------------------------------------------------
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Department, Event, Post, Notification, AuditLog

# Initialize Blueprint
admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin", template_folder="templates")

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        flash("Access denied — admin privileges required.", "danger")
        return redirect(url_for("core.index"))

    users = User.query.count()
    departments = Department.query.count()
    events = Event.query.count()
    posts = Post.query.count()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        users=users,
        departments=departments,
        events=events,
        posts=posts,
        logs=logs,
        title="Admin Dashboard",
    )

# ---------------------------------------------------------
# Manage Users
# ---------------------------------------------------------
@admin_bp.route("/users")
@login_required
def manage_users():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("core.index"))

    all_users = User.query.all()
    return render_template("admin/manage_users.html", users=all_users, title="Manage Users")

# ---------------------------------------------------------
# Manage Departments
# ---------------------------------------------------------
@admin_bp.route("/departments")
@login_required
def manage_departments():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("core.index"))

    all_departments = Department.query.all()
    return render_template("admin/manage_departments.html", departments=all_departments, title="Departments")

# ---------------------------------------------------------
# View Audit Logs
# ---------------------------------------------------------
@admin_bp.route("/audit-logs")
@login_required
def audit_logs():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("core.index"))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template("admin/audit_logs.html", logs=logs, title="Audit Logs")

# ---------------------------------------------------------
# Delete User
# ---------------------------------------------------------
@admin_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("admin_bp.dashboard"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash(f"User '{user.full_name}' deleted successfully.", "success")
    return redirect(url_for("admin_bp.manage_users"))

# ---------------------------------------------------------
# Utility Route for Testing
# ---------------------------------------------------------
@admin_bp.route("/ping")
def ping():
    return "🦍 Admin Blueprint active!"
