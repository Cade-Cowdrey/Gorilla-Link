# =============================================================
# FILE: blueprints/core/routes.py
# PittState-Connect — Core Pages & Contact System
# Includes home, about, contact form (with email automation).
# =============================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_pro import db
from models import ContactMessage
from utils.mail_util import send_email

core_bp = Blueprint("core_bp", __name__, url_prefix="/")

# -------------------------------------------------------------
# HOME PAGE
# -------------------------------------------------------------
@core_bp.route("/")
def home():
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Connecting students, alumni, and employers in the Gorilla Nation.",
    }
    panels = [
        {"icon": "fa-user-graduate", "title": "Students", "text": "Find jobs, scholarships, and mentors."},
        {"icon": "fa-handshake", "title": "Alumni", "text": "Give back, mentor students, and connect."},
        {"icon": "fa-building", "title": "Employers", "text": "Recruit Gorillas and post opportunities."},
    ]
    return render_template("core/home.html", hero=hero, panels=panels)


# -------------------------------------------------------------
# ABOUT PAGE
# -------------------------------------------------------------
@core_bp.route("/about")
def about():
    return render_template("core/about.html")


# -------------------------------------------------------------
# CONTACT PAGE
# -------------------------------------------------------------
@core_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        if not all([name, email, subject, message]):
            flash("⚠️ Please fill out all fields.", "warning")
            return redirect(url_for("core_bp.contact"))

        # Save to DB
        contact_msg = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(contact_msg)
        db.session.commit()

        # Auto-confirmation email (to sender)
        send_email(
            subject=f"Thank you for contacting PittState-Connect!",
            recipients=[email],
            template_name="emails/contact_confirmation.html",
            context={"name": name, "subject": subject, "message": message},
        )

        # Admin notification
        send_email(
            subject=f"📩 New Contact Message: {subject}",
            recipients=["admin@pittstate.edu"],
            text_body=f"From: {name} <{email}>\n\n{message}",
        )

        flash("✅ Your message has been sent successfully!", "success")
        return redirect(url_for("core_bp.contact"))

    return render_template("core/contact.html")
