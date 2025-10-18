from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required
from models import db, Company, JobInternship, Department
from utils.security_util import require_roles

career_bp = Blueprint("career", __name__, url_prefix="/career")

@career_bp.route("/", methods=["GET"])
def index():
    jobs = JobInternship.query.order_by(JobInternship.posted_at.desc()).limit(20).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Careers · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Careers & Internships</h1>
      <div class="mt-6 grid md:grid-cols-2 gap-4">
        {% for j in jobs %}
          <div class="bg-white dark:bg-[#1b1b1b] rounded-xl p-4 shadow">
            <h3 class="font-semibold">{{ j.title }}</h3>
            <p class="text-sm text-gray-500">{{ j.location or 'On-site' }}</p>
          </div>
        {% else %}
          <p class="text-gray-500">No jobs yet.</p>
        {% endfor %}
      </div>
    {% endblock %}
    """
    return render_template_string(html, jobs=jobs)

# API
@career_bp.route("/api", methods=["GET"])
def api_list():
    items = JobInternship.query.order_by(JobInternship.posted_at.desc()).all()
    return jsonify([{
        "id": i.id, "title": i.title, "company_id": i.company_id, "department_id": i.department_id,
        "location": i.location, "posted_at": i.posted_at.isoformat()
    } for i in items])

@career_bp.route("/api", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def api_create():
    data = request.get_json(force=True)
    j = JobInternship(
        title=data.get("title"),
        company_id=data.get("company_id"),
        department_id=data.get("department_id"),
        location=data.get("location")
    )
    db.session.add(j); db.session.commit()
    return jsonify({"ok": True, "id": j.id})
