from flask import Blueprint, render_template, current_app

core_bp = Blueprint('core_bp', __name__, template_folder='templates')

@core_bp.route('/')
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
        {"icon": "fa-handshake", "title": "Mentorships", "desc": "Pair with successful alumni mentors."},
    ]
    return render_template("core/home.html", hero=hero, panels=panels)

@core_bp.route('/about')
def about():
    """Overview of how PittState-Connect works."""
    overview = {
        "title": "How PittState-Connect Works",
        "intro": "A unified digital ecosystem for PSU students, alumni, and employers.",
        "sections": [
            {
                "title": "For Students",
                "points": [
                    "Smart scholarship matching using AI recommendations.",
                    "Auto-reminders for deadlines and essay guidance.",
                    "Career dashboards that visualize your growth."
                ]
            },
            {
                "title": "For Alumni",
                "points": [
                    "Reconnect with your department and mentor students.",
                    "Showcase your achievements on the Gorilla Scholars leaderboard.",
                    "Give back through targeted donor campaigns."
                ]
            },
            {
                "title": "For Employers",
                "points": [
                    "Post jobs, internships, and sponsorships directly.",
                    "View verified PSU talent pipelines.",
                    "Partner in the Gorilla Network for visibility."
                ]
            }
        ]
    }
    return render_template("core/about.html", overview=overview)

# Optional: lightweight diagnostics route
@core_bp.route('/ping')
def ping():
    return {"status": "ok", "service": "PittState-Connect Core"}
