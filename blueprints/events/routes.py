from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Event, User, Department
from datetime import datetime

events = Blueprint("events", __name__, template_folder="templates")

# ----------------------------------------
# 🌍 PUBLIC EVENTS LIST
# ----------------------------------------
@events.route("/events")
def events_public():
    """Public PSU-branded event listing (upcoming + past)."""
    upcoming_events = (
        Event.query.filter(Event.start_date >= datetime.utcnow())
        .order_by(Event.start_date.asc())
        .all()
    )
    past_events = (
        Event.query.filter(Event.start_date < datetime.utcnow())
        .order_by(Event.start_date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "core/events.html",
        upcoming_events=upcoming_events,
        past_events=past_events,
    )


# ----------------------------------------
# 🧾 EVENT DETAIL PAGE
# ----------------------------------------
@events.route("/events/<int:event_id>")
def event_detail(event_id):
    """Detailed page for a specific event."""
    event = Event.query.get_or_404(event_id)
    attendees = getattr(event, "attendees", [])
    department = Department.query.get(event.department_id) if event.department_id else None

    return render_template(
        "events/detail.html",
        event=event,
        attendees=attendees,
        department=department,
    )


# ----------------------------------------
# 🧠 ADMIN EVENTS DASHBOARD
# ----------------------------------------
@events.route("/events/dashboard")
@login_required
def events_dashboard():
    """Admin/faculty dashboard for event management and analytics."""
    if not getattr(current_user, "is_admin", False) and current_user.role not in ["faculty", "staff"]:
        flash("Admin or faculty access required.", "warning")
        return redirect(url_for("core.home"))

    total_events = Event.query.count()
    upcoming = Event.query.filter(Event.start_date >= datetime.utcnow()).count()
    past = Event.query.filter(Event.start_date < datetime.utcnow()).count()

    recent_events = Event.query.order_by(Event.start_date.desc()).limit(10).all()
    departments = Department.query.all()

    return render_template(
        "events/dashboard.html",
        total_events=total_events,
        upcoming=upcoming,
        past=past,
        recent_events=recent_events,
        departments=departments,
    )


# ----------------------------------------
# 🆕 CREATE EVENT
# ----------------------------------------
@events.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    """Allows admins or faculty to create a new event."""
    if not getattr(current_user, "is_admin", False) and current_user.role not in ["faculty", "staff"]:
        flash("Only admins or faculty can create events.", "danger")
        return redirect(url_for("events.events_public"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        start_date = request.form.get("start_date")
        location = request.form.get("location")
        department_id = request.form.get("department_id")

        if not title or not start_date:
            flash("Title and date are required.", "warning")
            return redirect(url_for("events.create_event"))

        new_event = Event(
            title=title,
            description=description,
            start_date=start_date,
            location=location,
            department_id=department_id if department_id else None,
            created_by=current_user.id,
        )
        db.session.add(new_event)
        db.session.commit()

        flash(f"Event '{title}' created successfully!", "success")
        return redirect(url_for("events.events_dashboard"))

    departments = Department.query.all()
    return render_template("events/create.html", departments=departments)


# ----------------------------------------
# 📝 REGISTER / RSVP FOR EVENT
# ----------------------------------------
@events.route("/events/register/<int:event_id>", methods=["POST"])
@login_required
def register_for_event(event_id):
    """Registers current user for a specific event."""
    event = Event.query.get_or_404(event_id)
    if current_user in event.attendees:
        flash("You are already registered for this event.", "info")
        return redirect(url_for("events.event_detail", event_id=event.id))

    event.attendees.append(current_user)
    db.session.commit()

    flash(f"You’ve registered for {event.title}!", "success")
    return redirect(url_for("events.event_detail", event_id=event.id))


# ----------------------------------------
# ❌ UNREGISTER FROM EVENT
# ----------------------------------------
@events.route("/events/unregister/<int:event_id>", methods=["POST"])
@login_required
def unregister_from_event(event_id):
    """Allows a user to cancel their event registration."""
    event = Event.query.get_or_404(event_id)
    if current_user not in event.attendees:
        flash("You weren’t registered for this event.", "info")
        return redirect(url_for("events.event_detail", event_id=event.id))

    event.attendees.remove(current_user)
    db.session.commit()

    flash(f"You’ve been unregistered from {event.title}.", "info")
    return redirect(url_for("events.event_detail", event_id=event.id))


# ----------------------------------------
# 🗑️ DELETE EVENT (ADMIN)
# ----------------------------------------
@events.route("/events/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    """Allows admins to delete an event."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("events.events_dashboard"))

    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()

    flash(f"Event '{event.title}' deleted successfully.", "info")
    return redirect(url_for("events.events_dashboard"))


# ----------------------------------------
# 📊 JSON ANALYTICS ENDPOINT
# ----------------------------------------
@events.route("/events/data")
@login_required
def events_data():
    """Provides JSON analytics data for events (for charts)."""
    total_events = Event.query.count()
    upcoming = Event.query.filter(Event.start_date >= datetime.utcnow()).count()
    past = Event.query.filter(Event.start_date < datetime.utcnow()).count()
    department_counts = (
        db.session.query(Department.name, db.func.count(Event.id))
        .outerjoin(Event, Department.id == Event.department_id)
        .group_by(Department.name)
        .all()
    )

    department_stats = [{"department": d, "event_count": c} for d, c in department_counts]

    return jsonify({
        "total": total_events,
        "upcoming": upcoming,
        "past": past,
        "by_department": department_stats,
    })


# ----------------------------------------
# 🚀 REDIRECT BASE /EVENTS TO PUBLIC VIEW
# ----------------------------------------
@events.route("/")
def redirect_root():
    """Redirects /events/ base path to the public listing."""
    return redirect(url_for("events.events_public"))
