from flask import Blueprint, render_template

core_bp = Blueprint("core_bp", __name__, template_folder="templates")

@core_bp.route("/")
def home():
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Your gateway to PSU scholarships, careers, and connections."
    }
    panels = [
        {
            "title": "Scholarships",
            "icon": "🎓",
            "desc": "Find and apply for scholarships tailored to your goals."
        },
        {
            "title": "Careers",
            "icon": "💼",
            "desc": "Discover jobs, internships, and employer partnerships."
        },
        {
            "title": "Community",
            "icon": "🦍",
            "desc": "Engage with students, alumni, and faculty across PSU."
        }
    ]
    return render_template("core/home.html", hero=hero, panels=panels)

@core_bp.route("/team")
def team():
    """Team page displaying project contributors and PSU branding."""
    team_members = [
        {
            "name": "Cade Cowdrey",
            "role": "Founder & Lead Developer",
            "bio": "Building PSU’s next-gen networking ecosystem for students, alumni, and employers."
        },
        {
            "name": "Connor Vandenberg",
            "role": "Project Lead & Strategic Developer",
            "bio": "Focused on innovation, branding, and partnerships for PittState-Connect."
        },
        {
            "name": "Pittsburg State University",
            "role": "Partner Institution",
            "bio": "Empowering students and alumni through connection, opportunity, and collaboration."
        },
    ]
    return render_template("core/team.html", title="Meet the Team", team=team_members)
