from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import User, Department, Event, Post, Notification, AuditLog
from datetime import datetime

admin = Blueprint("admin", __name__, template_folder="templates")

# ----------------------------------------
# 🛡️ ADMIN ACCESS CONTROL
# ----------------------------------------
def admin_required(func):
    """Decorator to restrict routes to admin users only."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access only.", "warning")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper


# ----------------------------------------
# 🧩 ADMIN DASHBOARD & INDEX
# ----------------------------------------
@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Main administrative dashboard overview."""
    total_users = User.query.count()
    total_departments = Department.query.count()
    total_events = Event.query.count()
    total_posts = Post.query.count()

    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        "admin/admin_dashboard.html",
        total_users=total_users,
        total_departments=total_departments,
        total_events=total_events,
        total_posts=total_posts,
        recent_logs=recent_logs,
        recent_users=recent_users
    )


@admin.route("/admin-preview")
@login_required
@admin_required
def admin_index():
    """Lists and previews all admin templates."""
    return render_template("admin/admin_index.html")


# ----------------------------------------
# 📊 ANALYTICS & INSIGHTS
# ----------------------------------------
@admin.route("/analytics")
@login_required
@admin_required
def analytics_dashboard():
    """Displays analytics overview for user engagement, activity, and growth."""
    users = User.query.count()
    alumni = User.query.filter_by(role="alumni").count()
    students = User.query.filter_by(role="student").count()
    events = Event.query.count()

    return render_template(
        "analytics/insights_dashboard.html",
        users=users,
        alumni=alumni,
        students=students,
        events=events,
    )


@admin.route("/analytics/data")
@login_required
@admin_required
def analytics_data():
    """Provides JSON stats for frontend analytics visualizations."""
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_events = Event.query.count()
    total_notifications = Notification.query.count()

    return jsonify({
        "users": total_users,
        "posts": total_posts,
        "events": total_events,
        "notifications": total_notifications,
    })


# ----------------------------------------
# 👥 USER MANAGEMENT
# ----------------------------------------
@admin.route("/users")
@login_required
@admin_required
def user_management():
    """Displays all users and their roles."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/user_management.html", users=users)


@admin.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activates or deactivates a user account."""
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    flash(f"User {user.name}'s active status updated.", "info")
    return redirect(url_for("admin.user_management"))


# ----------------------------------------
# 🏛️ DEPARTMENT MANAGEMENT
# ----------------------------------------
@admin.route("/departments")
@login_required
@admin_required
def departments():
    """Displays all academic departments."""
    departments = Department.query.all()
    return render_template("admin/departments_admin.html", departments=departments)


@admin.route("/departments/add", methods=["POST"])
@login_required
@admin_required
def add_department():
    """Adds a new department."""
    name = request.form.get("name")
    if not name:
        flash("Department name cannot be empty.", "warning")
        return redirect(url_for("admin.departments"))

    department = Department(name=name)
    db.session.add(department)
    db.session.commit()
    flash(f"Department '{name}' added successfully!", "success")
    return redirect(url_for("admin.departments"))


# ----------------------------------------
# 🎟️ EVENT MANAGEMENT
# ----------------------------------------
@admin.route("/events")
@login_required
@admin_required
def events():
    """Admin view of PSU events."""
    events = Event.query.order_by(Event.start_date.desc()).all()
    return render_template("admin/event_management.html", events=events)


@admin.route("/events/add", methods=["POST"])
@login_required
@admin_required
def add_event():
    """Creates a new event."""
    title = request.form.get("title")
    description = request.form.get("description")
    date = request.form.get("date")

    if not title or not date:
        flash("Event title and date are required.", "warning")
        return redirect(url_for("admin.events"))

    new_event = Event(title=title, description=description, start_date=date)
    db.session.add(new_event)
    db.session.commit()

    flash(f"Event '{title}' added successfully!", "success")
    return redirect(url_for("admin.events"))


# ----------------------------------------
# 📑 REPORTING
# ----------------------------------------
@admin.route("/reports")
@login_required
@admin_required
def reports():
    """Displays platform reports and summaries."""
    users = User.query.count()
    posts = Post.query.count()
    events = Event.query.count()
    departments = Department.query.count()
    return render_template(
        "admin/reports_overview.html",
        users=users,
        posts=posts,
        events=events,
        departments=departments
    )


# ----------------------------------------
# 🕵️ AUDIT LOGS
# ----------------------------------------
@admin.route("/audit-log")
@login_required
@admin_required
def audit_log():
    """Displays system audit log entries."""
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template("admin/audit_log.html", logs=logs)
