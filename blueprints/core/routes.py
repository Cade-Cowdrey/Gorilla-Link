from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import current_user
from extensions import db
from models import User, Department, Event, Post
from datetime import datetime

core = Blueprint("core", __name__, template_folder="templates")


# ----------------------------------------
# 🏠 HOME PAGE
# ----------------------------------------
@core.route("/")
def home():
    """Landing page of PittState-Connect."""
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.filter(Event.start_date >= datetime.utcnow()).limit(3).all()
    department_count = Department.query.count()
    user_count = User.query.count()

    return render_template(
        "core/home.html",
        recent_posts=recent_posts,
        upcoming_events=upcoming_events,
        department_count=department_count,
        user_count=user_count,
    )


# ----------------------------------------
# 👥 TEAM PAGE
# ----------------------------------------
@core.route("/team")
def team():
    """Displays the PittState-Connect development and leadership team."""
    admins = User.query.filter_by(is_admin=True).all()
    faculty = User.query.filter_by(role="faculty").limit(6).all()

    return render_template(
        "core/team.html",
        admins=admins,
        faculty=faculty,
    )


# ----------------------------------------
# 💼 CAREERS PAGE
# ----------------------------------------
@core.route("/careers")
def careers():
    """Public page listing PSU career and internship opportunities."""
    departments = Department.query.all()
    job_posts = Post.query.filter_by(category="career").order_by(Post.created_at.desc()).limit(10).all()

    return render_template(
        "core/careers.html",
        departments=departments,
        job_posts=job_posts,
    )


# ----------------------------------------
# 🎟️ EVENTS PAGE
# ----------------------------------------
@core.route("/events")
def events():
    """Displays all campus and alumni events."""
    upcoming_events = Event.query.filter(Event.start_date >= datetime.utcnow()).order_by(Event.start_date.asc()).all()
    past_events = Event.query.filter(Event.start_date < datetime.utcnow()).order_by(Event.start_date.desc()).limit(5).all()

    return render_template(
        "core/events.html",
        upcoming_events=upcoming_events,
        past_events=past_events,
    )


# ----------------------------------------
# 🏛️ ABOUT PAGE
# ----------------------------------------
@core.route("/about")
def about():
    """Public About page with mission, history, and PSU branding."""
    total_users = User.query.count()
    total_departments = Department.query.count()
    total_events = Event.query.count()

    return render_template(
        "core/about.html",
        total_users=total_users,
        total_departments=total_departments,
        total_events=total_events,
    )


# ----------------------------------------
# ✉️ CONTACT PAGE
# ----------------------------------------
@core.route("/contact", methods=["GET", "POST"])
def contact():
    """Public Contact page for inquiries or support."""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("Please fill out all fields before submitting.", "warning")
            return redirect(url_for("core.contact"))

        # Optionally save or forward the message
        print(f"📩 New contact form submission: {name} ({email}) — {message}")
        flash("Thank you for contacting us! We’ll respond shortly.", "success")
        return redirect(url_for("core.contact"))

    return render_template("core/contact.html")


# ----------------------------------------
# 📬 EMAIL PREVIEWS INDEX
# ----------------------------------------
@core.route("/email-previews")
def email_previews():
    """Displays list of PSU-branded email templates for QA or design."""
    return render_template("emails/index.html")


# ----------------------------------------
# 🗂️ MASTER TEMPLATE INDEX
# ----------------------------------------
@core.route("/template-master")
def template_master_index():
    """Central dashboard linking to all system template hubs."""
    return render_template("core/template_master_index.html")


# ----------------------------------------
# 🧾 HEALTH CHECK ENDPOINT
# ----------------------------------------
@core.route("/health")
def health_check():
    """Lightweight JSON endpoint for uptime monitoring."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "active_users": User.query.count(),
        "total_departments": Department.query.count()
    })
