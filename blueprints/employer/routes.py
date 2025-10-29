# File: blueprints/employer/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("employer", __name__, url_prefix="/employer")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="employer")

@bp.get("/")
def index():
    track_page_view("employer")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Employers | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Employers</h1>
        <p class="text-muted">Sponsorships, job postings, and talent search.</p>
      </div>
    {% endblock %}
    """)
