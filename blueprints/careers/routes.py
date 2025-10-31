# File: blueprints/careers/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import record_page_view

bp = Blueprint("careers_bp", __name__, url_prefix="/careers")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="careers")

@bp.get("/")
def index():
    record_page_view("careers")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Careers | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Careers</h1>
        <p class="text-muted">Jobs, internships, and recruiter connections.</p>
      </div>
    {% endblock %}
    """)
