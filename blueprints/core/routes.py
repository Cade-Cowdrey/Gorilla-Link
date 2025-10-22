# =============================================================
# FILE: blueprints/core/routes.py
# Core pages: home, about, contact, ping, and 404 fallback.
# Handles PSU branding, SmartMatch overview, and contact form.
# =============================================================

from flask import (
    Blueprint,
    render_template,
    current_app,
    redirect,
    url_for,
    request,
    flash,
)
from utils.mail_util import send_email
from models import db, ContactMessage

core_bp = Blueprint("core_bp", __name__, url_prefix="")

# -------------------------------------------------------------
# HOME PAGE
# -------------------------------------------------------------
@core_bp.route("/")
def home():
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Empowering Gorillas with smarter networking, scholarships, and career tools.",
        "cta_text": "Get Started",
        "cta_link": "/auth/register",
    }
    panels = [
        {"icon": "fa-users", "title": "Connect", "desc": "Network with students, alumni, and employers."},
        {"icon": "fa-graduation-cap", "title": "Scholarships", "desc": "Discover and apply with SmartMatch AI."},
        {"icon": "fa-chart-line", "title": "Analytics", "desc": "Track career and funding progress in real time."},
        {"icon": "fa-handshake", "title": "Mentorships", "desc": "Pair with successful alumni mentors and recruiters."},
    ]
    return render_template("core/home.html", hero=hero, panels=panels)


# -------------------------------------------------------------
# ABOUT PAGE
# -------------------------------------------------------------
@core_bp.route("/about")
def about():
    overview = {
        "title": "How PittState-Connect Works",
        "intro": "A unified digital ecosystem for PSU students, alumni, and employers.",
    }
    return render_template("core/about.html", overview=overview)


# -------------------------------------------------------------
# CONTACT PAGE (GET + POST)
# -------------------------------------------------------------
@core_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "No subject").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, message]):
            flash("❌ Please fill out all fields before submitting.", "danger")
            return redirect(url_for("core_bp.contact"))

        # Save message to DB
        new_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )
        db.session.add(new_msg)
        db.session.commit()

        # Send notification email to admin
        try:
            send_email(
                subject=f"[PittState-Connect] {subject}",
                recipients=["admin@pittstateconnect.edu"],
                body=f"New message from {name} <{email}>:\n\n{message}",
            )
            flash("✅ Your message has been sent successfully!", "success")
        except Exception as e:
            current_app.logger.error(f"Mail send failed: {e}")
            flash("⚠️ Message saved but email failed to send.", "warning")

        return redirect(url_for("core_bp.contact"))

    return render_template("core/contact.html")


# -------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------
@core_bp.route("/ping")
def ping():
    return {"status": "ok", "service": "PittState-Connect Core"}


# -------------------------------------------------------------
# GLOBAL 404 FALLBACK
# -------------------------------------------------------------
@core_bp.app_errorhandler(404)
def not_found(e):
    current_app.logger.warning(f"404 redirected: {e}")
    return redirect(url_for("core_bp.home"))
