from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Notification, User, Post, Event
from datetime import datetime

notifications = Blueprint("notifications", __name__, template_folder="templates")

# ----------------------------------------
# 📬 USER NOTIFICATIONS DASHBOARD
# ----------------------------------------
@notifications.route("/notifications")
@login_required
def notifications_dashboard():
    """Displays the logged-in user's notifications."""
    user_notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        "notifications/dashboard.html",
        notifications=user_notifications,
        unread_count=unread_count,
    )


# ----------------------------------------
# 👀 MARK AS READ
# ----------------------------------------
@notifications.route("/notifications/read/<int:notification_id>", methods=["POST"])
@login_required
def mark_as_read(notification_id):
    """Marks a single notification as read."""
    note = Notification.query.get_or_404(notification_id)
    if note.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("notifications.notifications_dashboard"))

    note.is_read = True
    db.session.commit()
    return jsonify({"success": True})


# ----------------------------------------
# 🧹 CLEAR ALL NOTIFICATIONS
# ----------------------------------------
@notifications.route("/notifications/clear", methods=["POST"])
@login_required
def clear_notifications():
    """Deletes all notifications for the logged-in user."""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("All notifications cleared.", "info")
    return redirect(url_for("notifications.notifications_dashboard"))


# ----------------------------------------
# 🧠 ADMIN NOTIFICATION PANEL
# ----------------------------------------
@notifications.route("/notifications/admin")
@login_required
def admin_notifications_panel():
    """Admin dashboard for viewing and managing system-wide notifications."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access only.", "warning")
        return redirect(url_for("notifications.notifications_dashboard"))

    all_notifications = (
        Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    )
    users = User.query.order_by(User.name.asc()).all()

    return render_template(
        "notifications/admin_panel.html",
        notifications=all_notifications,
        users=users,
    )


# ----------------------------------------
# 📨 SEND ADMIN ANNOUNCEMENT
# ----------------------------------------
@notifications.route("/notifications/send", methods=["POST"])
@login_required
def send_announcement():
    """Allows admins to send announcements to all users."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("notifications.admin_notifications_panel"))

    message = request.form.get("message")
    if not message:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("notifications.admin_notifications_panel"))

    users = User.query.all()
    now = datetime.utcnow()

    for user in users:
        note = Notification(
            user_id=user.id,
            title="Admin Announcement",
            message=message,
            link=url_for("core.home"),
            created_at=now,
        )
        db.session.add(note)
    db.session.commit()

    flash("Announcement sent to all users successfully!", "success")
    return redirect(url_for("notifications.admin_notifications_panel"))


# ----------------------------------------
# 🔄 EVENT REMINDERS (AUTO-GENERATED)
# ----------------------------------------
@notifications.route("/notifications/generate-events")
@login_required
def generate_event_notifications():
    """Generates notifications for upcoming events (admin tool)."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("notifications.admin_notifications_panel"))

    upcoming_events = Event.query.filter(Event.start_date >= datetime.utcnow()).all()
    for event in upcoming_events:
        attendees = getattr(event, "attendees", [])
        for attendee in attendees:
            existing = Notification.query.filter_by(
                user_id=attendee.id,
                title="Event Reminder",
                link=url_for("events.event_detail", event_id=event.id)
            ).first()
            if not existing:
                db.session.add(Notification(
                    user_id=attendee.id,
                    title="Event Reminder",
                    message=f"Upcoming event: {event.title} on {event.start_date.strftime('%b %d, %Y')}.",
                    link=url_for("events.event_detail", event_id=event.id),
                    created_at=datetime.utcnow(),
                ))
    db.session.commit()
    flash("Event reminders generated successfully.", "success")
    return redirect(url_for("notifications.admin_notifications_panel"))


# ----------------------------------------
# 📊 NOTIFICATION ANALYTICS (JSON)
# ----------------------------------------
@notifications.route("/notifications/data")
@login_required
def notifications_data():
    """Provides JSON data for analytics dashboards."""
    total = Notification.query.filter_by(user_id=current_user.id).count()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    types = (
        db.session.query(Notification.title, db.func.count(Notification.id))
        .filter_by(user_id=current_user.id)
        .group_by(Notification.title)
        .all()
    )

    return jsonify({
        "total": total,
        "unread": unread,
        "by_type": [{"type": t, "count": c} for t, c in types]
    })


# ----------------------------------------
# 🚀 ROOT REDIRECT
# ----------------------------------------
@notifications.route("/")
def notifications_root_redirect():
    """Redirect base /notifications route to dashboard."""
    return redirect(url_for("notifications.notifications_dashboard"))
