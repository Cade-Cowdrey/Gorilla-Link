from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import limiter
from utils.analytics_util import record_page_view

# Scholarships blueprint for handling scholarship hub features
bp = Blueprint("scholarships_bp", __name__, url_prefix="/scholarships")

@bp.route("/")
@limiter.limit("20/minute")
@login_required
def index():
    """Scholarships home page showing hub overview."""
    record_page_view("scholarships_home", current_user.id if current_user.is_authenticated else None)
    return render_template("scholarships/index.html", title="Scholarships Hub | PittState-Connect")

@bp.route("/browse")
@login_required
def browse():
    """List available scholarships with basic details."""
    record_page_view("scholarships_browse", current_user.id if current_user.is_authenticated else None)
    scholarships = [
        {"id": 1, "name": "Full Ride Scholarship", "deadline": "2025-05-01", "amount": 10000},
        {"id": 2, "name": "STEM Excellence Award", "deadline": "2025-03-15", "amount": 5000},
        {"id": 3, "name": "Leadership Grant", "deadline": "2025-04-30", "amount": 2500},
    ]
    return render_template("scholarships/browse.html", scholarships=scholarships, title="Browse Scholarships | PittState-Connect")

@bp.route("/my")
@login_required
def my_scholarships():
    """Display scholarships the current user has saved or applied to."""
    record_page_view("scholarships_my", current_user.id if current_user.is_authenticated else None)
    # In a real application this would query the database for the user's scholarships
    my_sch = []
    return render_template("scholarships/my_scholarships.html", scholarships=my_sch, title="My Scholarships | PittState-Connect")

@bp.route("/apply/<int:scholarship_id>", methods=["GET", "POST"])
@login_required
def apply(scholarship_id: int):
    """Allow a user to apply to a scholarship; currently a placeholder stub."""
    record_page_view("scholarships_apply", current_user.id if current_user.is_authenticated else None)
    # This stub simply flashes a message and redirects back to browse
    flash("Application submitted successfully! (stub)", "success")
    return redirect(url_for("scholarships_bp.browse"))
