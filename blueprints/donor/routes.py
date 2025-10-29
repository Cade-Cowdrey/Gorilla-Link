# File: blueprints/donor/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("donor", __name__, url_prefix="/donor")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="donor")

@bp.get("/")
def index():
    track_page_view("donor")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Donor Portal | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Donor Portal</h1>
        <p class="text-muted">Sponsor programs, scholarships, and impact reports.</p>
      </div>
    {% endblock %}
    """)
