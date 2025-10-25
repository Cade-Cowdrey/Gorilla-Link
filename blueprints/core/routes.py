from flask import Blueprint, render_template, current_app

core_bp = Blueprint("core_bp", __name__, template_folder="../../templates/core")

@core_bp.route("/")
@core_bp.route("/index")
def home():
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Your hub for scholarships, careers, mentors, and alumni connections.",
        "cta_text": "Explore Opportunities",
        "cta_link": "/careers"
    }

    panels = [
        {"title": "Scholarship Hub", "desc": "Discover funding and apply with ease.", "icon": "bi-award"},
        {"title": "Career Center", "desc": "Find internships and high-paying jobs.", "icon": "bi-briefcase"},
        {"title": "Analytics Dashboard", "desc": "Track progress and insights.", "icon": "bi-graph-up"},
        {"title": "Alumni Network", "desc": "Connect with successful Gorillas worldwide.", "icon": "bi-people-fill"}
    ]

    current_app.logger.info("✅ Core home route rendered successfully.")
    return render_template("core/home.html", hero=hero, panels=panels)

@core_bp.route("/about")
def about():
    context = {
        "mission": "PittState-Connect empowers students, alumni, and employers through integrated data and opportunity pipelines.",
        "values": ["Innovation", "Accessibility", "Growth", "Community"],
    }
    return render_template("core/about.html", **context)
