# File: blueprints/mentors/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("mentors", __name__, url_prefix="/mentors")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="mentors")

@bp.get("/")
def index():
    track_page_view("mentors")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Mentors | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Mentors</h1>
        <p class="text-muted">Alumni & peer mentorship matchmaking.</p>
      </div>
    {% endblock %}
    """)
