# File: blueprints/students/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("students", __name__, url_prefix="/students")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="students")

@bp.get("/")
def index():
    track_page_view("students")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Students | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Students</h1>
        <p class="text-muted">Everything current students need in one place.</p>
      </div>
    {% endblock %}
    """)
