# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Admin Blueprint — PSU-Branded Dashboard & Controls
# ---------------------------------------------------------
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Department, Event, Post, Notification

# ---------------------------------------------------------
# Blueprint Definition
# ---------------------------------------------------------
admin_bp = Blueprint(
    "admin_bp",
    __name__,
    url_prefix="/admin",
    template_folder="templates"
)

# ---------------------------------------------------------
# Helper Access Control
# ---------------------------------------------------------
def admin_required():
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        flash("Access denied — Admin privileges required.", "danger")
        return False
    return True

# ---------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not admin_required():
        return redirect(url_for("core.index"))

    total_users = User.query.count()
    total_departments = Department.query.count()
    total_posts = Post.query.count()
    total_events = Event.query.count()
    total_notifications = Notification.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard | PittState-Connect",
        total_users=total_users,
        total_departments=total_departments,
        total_posts=total_posts,
        total_events=total_events,
        total_notifications=total_notifications,
        recent_users=recent_users,
        recent_posts=recent_posts,
    )

# ---------------------------------------------------------
# Manage Users
# ---------------------------------------------------------
@admin_bp.route("/users")
@login_required
def manage_users():
    if not admin_required():
        return redirect(url_for("core.index"))
    users = User.query.order_by(User.last_name.asc()).all()
    return render_template("admin/manage_users.html", users=users, title="Manage Users")

# ---------------------------------------------------------
# Manage Departments
# ---------------------------------------------------------
@admin_bp.route("/departments")
@login_required
def manage_departments():
    if not admin_required():
        return redirect(url_for("core.index"))
    departments = Department.query.all()
    return render_template("admin/manage_departments.html", departments=departments, title="Departments")

# ---------------------------------------------------------
# Manage Events
# ---------------------------------------------------------
@admin_bp.route("/events")
@login_required
def manage_events():
    if not admin_required():
        return redirect(url_for("core.index"))
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template("admin/manage_events.html", events=events, title="Manage Events")

# ---------------------------------------------------------
# Manage Notifications
# ---------------------------------------------------------
@admin_bp.route("/notifications")
@login_required
def manage_notifications():
    if not admin_required():
        return redirect(url_for("core.index"))
    notes = Notification.query.order_by(Notification.timestamp.desc()).all()
    return render_template("admin/manage_notifications.html", notifications=notes, title="Manage Notifications")

# ---------------------------------------------------------
# Delete a User
# ---------------------------------------------------------
@admin_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not admin_required():
        return redirect(url_for("admin_bp.dashboard"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.first_name} {user.last_name}' deleted successfully.", "success")

    return redirect(url_for("admin_bp.manage_users"))

# ---------------------------------------------------------
# Test / Health Route
# ---------------------------------------------------------
@admin_bp.route("/ping")
def ping():
    return "🦍 Admin Blueprint active and healthy!"
