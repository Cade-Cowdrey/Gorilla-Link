from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
import logging
import datetime
from utils.mail_util import send_system_alert
from utils.analytics_util import record_page_visit
from utils.ai_util import generate_ai_job_insight  # optional enhancement (AI helper)
from extensions import db
from models import Job, Department

careers_bp = Blueprint("careers_bp", __name__, url_prefix="/careers")
logger = logging.getLogger(__name__)

@careers_bp.before_request
def log_request():
    record_page_visit("careers")  # Analytics tracking
    logger.info(f"📊 Careers page accessed by user: {getattr(current_user, 'email', 'guest')}")

@careers_bp.route("/")
def index():
    """Career hub dashboard – job listings, featured employers, and analytics."""
    try:
        jobs = Job.query.order_by(Job.date_posted.desc()).limit(12).all()
        featured_depts = Department.query.limit(6).all()
        return render_template(
            "careers/index.html",
            jobs=jobs,
            featured_depts=featured_depts,
            page_title="PittState Careers Hub",
            meta_description="Explore Pitt State internships, job opportunities, and career resources.",
            ai_enabled=True,
        )
    except Exception as e:
        logger.error(f"Error loading careers hub: {e}")
        send_system_alert("Career Hub Error", str(e))
        return render_template("errors/500.html"), 500


@careers_bp.route("/job/<int:job_id>")
@login_required
def job_detail(job_id):
    """Display job detail page with optional AI-generated job match insights."""
    try:
        job = Job.query.get_or_404(job_id)
        ai_summary = None
        if current_app.config.get("ENABLE_AI_ASSIST", True):
            ai_summary = generate_ai_job_insight(job.title, job.description)
        return render_template(
            "careers/job_detail.html",
            job=job,
            ai_summary=ai_summary,
            page_title=f"{job.title} | PittState Careers",
        )
    except Exception as e:
        logger.exception(f"Failed to render job detail: {e}")
        send_system_alert("Job Detail Error", str(e))
        return render_template("errors/500.html"), 500


@careers_bp.route("/api/jobs")
def api_jobs():
    """Return JSON list of jobs for frontend dashboards."""
    try:
        jobs = Job.query.order_by(Job.date_posted.desc()).all()
        job_list = [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "department": j.department.name if j.department else "General",
                "date_posted": j.date_posted.strftime("%Y-%m-%d"),
                "description": j.description[:200] + "...",
            }
            for j in jobs
        ]
        return jsonify({"jobs": job_list})
    except Exception as e:
        logger.error(f"Job API error: {e}")
        return jsonify({"error": "Failed to load jobs"}), 500


@careers_bp.app_errorhandler(404)
def not_found_error(error):
    """Custom 404 for missing job posts."""
    logger.warning(f"Careers 404: {error}")
    return render_template("errors/404.html", page_title="Job Not Found"), 404
