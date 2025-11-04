# File: blueprints/careers/routes.py
from flask import Blueprint, render_template, jsonify
from utils.analytics_util import record_page_view

bp = Blueprint("careers_bp", __name__, url_prefix="/careers")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="careers")

@bp.get("/")
def index():
    record_page_view("careers")
    # Render proper template with empty data for now
    return render_template("careers/index.html", featured_jobs=[], employers=[])

@bp.get("/jobs")
def jobs():
    record_page_view("careers_jobs")
    return render_template("careers/jobs.html", jobs=[])
