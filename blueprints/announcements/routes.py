# blueprints/announcements/routes.py
from __future__ import annotations
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.audit import audit

announcements_bp = Blueprint("announcements_bp", __name__, url_prefix="/announcements")

@announcements_bp.get("/")
@login_required
def index():
    # Fetch from DB; placeholder list
    items = [
        {"title": "Fall Scholarship Window Open", "body": "Apply by Nov 10.", "audience": "students"},
        {"title": "Donor Summit", "body": "Join us Dec 2 at the Alumni Center.", "audience": "alumni"},
    ]
    return render_template("announcements/index.html", items=items)

@announcements_bp.post("/create")
@login_required
def create():
    # role check omitted for brevity
    title = request.form.get("title")
    body = request.form.get("body")
    audience = request.form.get("audience", "all")
    # persist to DB ...
    audit("create", "announcement", meta={"title": title, "audience": audience})
    flash("Announcement published.", "success")
    return redirect(url_for("announcements_bp.index"))
