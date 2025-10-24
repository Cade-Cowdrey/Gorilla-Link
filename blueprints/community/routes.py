from flask import render_template, Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user

community_bp = Blueprint("community_bp", __name__)

# ------------------------------
# Community Hub Overview
# ------------------------------
@community_bp.route("/")
def index():
    sections = [
        {"title": "Campus Feed", "desc": "Share updates, photos, and campus news with peers.", "icon": "feed"},
        {"title": "Gorilla Groups", "desc": "Join study, hobby, and professional groups.", "icon": "users"},
        {"title": "Mentorship Hub", "desc": "Connect with alumni mentors and peers.", "icon": "lightbulb"},
        {"title": "Discussion Boards", "desc": "Post questions and get advice on PSU life & careers.", "icon": "chat"},
    ]
    return render_template("community/index.html", sections=sections, title="PittState Community")

# ------------------------------
# Feed (Optional Enhancement)
# ------------------------------
@community_bp.route("/feed")
@login_required
def feed():
    # Placeholder logic for feed aggregation
    posts = [
        {"user": "Cade C.", "content": "Welcome to the new PittState-Connect feed!", "time": "5m ago"},
        {"user": "Alexis B.", "content": "Just accepted an internship at Garmin!", "time": "1h ago"},
        {"user": "Faculty Mentor", "content": "New research assistant openings in the Biology Dept.", "time": "3h ago"},
    ]
    return render_template("community/feed.html", posts=posts, title="Campus Feed")

# ------------------------------
# Groups
# ------------------------------
@community_bp.route("/groups")
@login_required
def groups():
    groups = [
        {"name": "Business Majors Network", "members": 142},
        {"name": "Future Teachers of America", "members": 98},
        {"name": "Gorilla Dev Club", "members": 230},
    ]
    return render_template("community/groups.html", groups=groups, title="Gorilla Groups")

# ------------------------------
# Mentorship Board
# ------------------------------
@community_bp.route("/mentorship")
@login_required
def mentorship():
    mentors = [
        {"name": "Dr. Harrison Wells", "field": "Engineering", "status": "Available"},
        {"name": "Rachel Kim", "field": "Business Analytics", "status": "Available"},
        {"name": "Jordan P.", "field": "Marketing", "status": "Unavailable"},
    ]
    return render_template("community/mentorship.html", mentors=mentors, title="Mentorship Hub")

# ------------------------------
# Discussion Board
# ------------------------------
@community_bp.route("/discussions")
@login_required
def discussions():
    threads = [
        {"topic": "Housing Near Campus", "posts": 42, "updated": "1h ago"},
        {"topic": "Best Study Spots in Kelce", "posts": 18, "updated": "3h ago"},
        {"topic": "Internship Resume Advice", "posts": 67, "updated": "6h ago"},
    ]
    return render_template("community/discussions.html", threads=threads, title="Discussion Boards")
