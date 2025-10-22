# =============================================================
# FILE: blueprints/core/routes.py
# PittState-Connect — Core Blueprint
# Handles main site pages: Home, About, Mission, and fallback routes.
# =============================================================

from flask import Blueprint, render_template, current_app, redirect, url_for

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
    """Overview of how PittState-Connect works."""
    overview = {
        "title": "How PittState-Connect Works",
        "intro": "A unified digital ecosystem for PSU students, alumni, and employers.",
        "sections": [
            {
                "title": "For Students",
                "points": [
                    "AI-powered scholarship SmartMatch recommender.",
                    "Auto reminders and deadline tracking dashboard.",
                    "Career analytics and funding progress visualization.",
                ],
            },
            {
                "title": "For Alumni",
                "points": [
                    "Reconnect with your department and mentor students.",
                    "Feature on the Gorilla Scholars leaderboard.",
                    "Contribute to scholarship and donor campaigns.",
                ],
            },
            {
                "title": "For Employers",
                "points": [
                    "Post verified jobs, internships, and sponsorships.",
                    "Gain access to PSU student and alumni pipelines.",
                    "Partner through the Gorilla Network to recruit top talent.",
                ],
            },
        ],
    }
    return render_template("core/about.html", overview=overview)


# -------------------------------------------------------------
# CONTACT / MISC
# -------------------------------------------------------------
@core_bp.route("/contact")
def contact():
    """Optional Contact page placeholder."""
    return render_template("core/contact.html")


# -------------------------------------------------------------
# HEALTH CHECK / DIAGNOSTIC
# -------------------------------------------------------------
@core_bp.route("/ping")
def ping():
    return {"status": "ok", "service": "PittState-Connect Core"}


# -------------------------------------------------------------
# FALLBACK REDIRECT
# -------------------------------------------------------------
@core_bp.app_errorhandler(404)
def not_found(e):
    """Redirects any invalid route to home for smoother UX."""
    current_app.logger.warning(f"404 on path redirected to home: {e}")
    return redirect(url_for("core_bp.home"))
