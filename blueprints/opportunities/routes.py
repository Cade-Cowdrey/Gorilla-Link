# File: blueprints/opportunities/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("opportunities", __name__, url_prefix="/opportunities")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="opportunities")

@bp.get("/")
def index():
    track_page_view("opportunities")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Opportunities | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Opportunities</h1>
        <p class="text-muted">Scholarships, grants, fellowships, and programs.</p>
      </div>
    {% endblock %}
    """)
