from flask import Blueprint, render_template
from models import JobOpportunity

career_bp = Blueprint("career", __name__, template_folder="templates/careers")

@career_bp.route("/careers")
def careers_dashboard():
    """Display PSU-branded job opportunities dashboard."""
    jobs = JobOpportunity.query.order_by(JobOpportunity.created_at.desc()).limit(20).all()
    return render_template("careers/dashboard.html", jobs=jobs, title="Career Opportunities | PittState-Connect")
