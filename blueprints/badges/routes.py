# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Badges Blueprint — Achievements & Recognition
# ---------------------------------------------------------
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User

badges_bp = Blueprint(
    "badges_bp",
    __name__,
    url_prefix="/badges",
    template_folder="templates"
)

# ---------------------------------------------------------
# Badges Dashboard
# ---------------------------------------------------------
@badges_bp.route("/dashboard")
@login_required
def dashboard():
    """Display PSU-branded badges dashboard."""
    users = User.query.all()
    return render_template(
        "badges/user_badges.html",
        title="Badges & Achievements | PittState-Connect",
        users=users,
    )

# ---------------------------------------------------------
# Award a Badge (Admin or Faculty)
# ---------------------------------------------------------
@badges_bp.route("/award/<int:user_id>/<string:badge_name>")
@login_required
def award_badge(user_id, badge_name):
    """Simulate awarding a badge to a user."""
    user = User.query.get_or_404(user_id)
    flash(f"🏅 {user.first_name} {user.last_name} earned the '{badge_name}' badge!", "success")
    return redirect(url_for("badges_bp.dashboard"))

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@badges_bp.route("/ping")
def ping():
    return "🦍 Badges blueprint active and healthy!"
