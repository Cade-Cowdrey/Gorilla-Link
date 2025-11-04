# File: blueprints/careers/routes.py
from flask import Blueprint, render_template, jsonify
from utils.analytics_util import record_page_view
from models import Job

bp = Blueprint("careers_bp", __name__, url_prefix="/careers")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="careers")

@bp.get("/")
def index():
    record_page_view("careers")
    # Get featured jobs (active jobs, limited to 6)
    featured_jobs = Job.query.filter_by(is_active=True).limit(6).all()
    return render_template("careers/index.html", featured_jobs=featured_jobs, employers=[])

@bp.get("/jobs")
def jobs():
    record_page_view("careers_jobs")
    # Get all active jobs
    all_jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_at.desc()).all()
    return render_template("careers/jobs.html", jobs=all_jobs)
