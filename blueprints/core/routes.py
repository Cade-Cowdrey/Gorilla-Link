# ============================================================
# FILE: blueprints/core/routes.py
# ============================================================
from flask import render_template, current_app
from . import core_bp

@core_bp.route("/", methods=["GET"])
def home():
    # Safe stub context; replace with DB pulls later.
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Connecting Students, Alumni, Mentors, and Employers",
    }
    panels = [
        {"title": "Scholarships", "url": "/scholarships"},
        {"title": "Careers", "url": "/careers"},
        {"title": "Mentors", "url": "/mentors"},
        {"title": "Alumni", "url": "/alumni"},
    ]
    return render_template("core/home.html", hero=hero, panels=panels)

@core_bp.route("/team", methods=["GET"])
def team():
    return render_template("core/team.html", team=[{"name": "PSU Dev Squad", "role": "Builders"}])

# Lightweight health passthrough (UI)
@core_bp.route("/health", methods=["GET"])
def health_ui():
    return render_template("core/health.html", app_name=current_app.config.get("APP_NAME", "PittState-Connect"))
