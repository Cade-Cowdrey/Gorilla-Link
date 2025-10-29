# File: blueprints/badges/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("badges", __name__, url_prefix="/badges")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="badges")

@bp.get("/")
def index():
    track_page_view("badges")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Badges | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Skill Badges</h1>
        <p class="text-muted">Earn PSU-verified badges for projects, internships, and service.</p>
      </div>
    {% endblock %}
    """)
