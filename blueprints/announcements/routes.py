# blueprints/announcements/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.analytics_util import record_page_view
from utils.audit import audit

bp = Blueprint("announcements_bp", __name__, url_prefix="/announcements")

@bp.get("/")
@login_required
def index():
    """Display a list of announcements."""
    record_page_view("announcements_index")
    items = [
        {"title": "Fall Scholarship Window Open", "body": "Apply by Nov 8.", "audience": "students"},
        {"title": "Donor Summit", "body": "Join us Dec 2 at the Alumni Center.", "audience": "alumni"},
    ]
    return render_template("announcements/index.html", items=items)

@bp.post("/create")
@login_required
def create():
    """Handle creation of a new announcement via form submission."""
    record_page_view("announcements_create")
    title = request.form.get("title")
    body = request.form.get("body")
    audience = request.form.get("audience", "all")
    # TODO: persist to DB
    audit("create", "announcement", meta={"title": title, "body": body, "audience": audience})
    flash("Announcement published.", "success")
    return redirect(url_for("announcements_bp.index"))
