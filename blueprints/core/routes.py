# blueprints/core/routes.py
from flask import Blueprint, render_template
from loguru import logger

core_bp = Blueprint("core_bp", __name__)

@core_bp.route("/", methods=["GET"])
def home():
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Your hub for scholarships, careers, mentors, and alumni connections.",
        "cta_text": "Explore Opportunities",
        "cta_href": "/scholarships/",
    }
    panels = [
        {"title": "Scholarship Hub", "desc": "Discover funding and apply with ease.", "icon": "bi-award"},
        {"title": "Career Center", "desc": "Internships, jobs, and skill-building.", "icon": "bi-briefcase"},
        {"title": "Mentors & Alumni", "desc": "Get guidance and grow your network.", "icon": "bi-people-fill"},
    ]
    logger.info("✅ Core home route rendered successfully.")
    return render_template("core/home.html", hero=hero, panels=panels)
