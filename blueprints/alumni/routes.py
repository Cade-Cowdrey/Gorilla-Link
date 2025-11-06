# File: blueprints/alumni/routes.py
from flask import Blueprint, render_template, jsonify
from utils.analytics_util import record_page_view

bp = Blueprint("alumni", __name__, url_prefix="/alumni")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="alumni")

@bp.get("/")
def index():
    # Log page view
    record_page_view("alumni_home")
    
    # Render a proper landing page for alumni
    return render_template("alumni/directory.html")
