# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Badges Blueprint — Achievements & Recognition
# ---------------------------------------------------------
from flask import Blueprint, render_template
from flask_login import login_required
from models import User

badges_bp = Blueprint(
    "badges_bp",
    __name__,
    url_prefix="/badges",
    template_folder="templates"
)

# ---------------------------------------------------------
# User Badges Dashboard
# ---------------------------------------------------------
@badges_bp.route("/dashboard")
@login_required
def dashboard():
    users = User.query.all()
    return render_template(
        "badges/user_badges.html",
        title="User Badges | PittState-Connect",
        users=users,
    )

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@badges_bp.route("/ping")
def ping():
    return "🦍 Badges Blueprint active and healthy!"
