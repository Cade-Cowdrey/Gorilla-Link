# File: blueprints/security/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("security", __name__, url_prefix="/security")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="security")

@bp.get("/")
def index():
    track_page_view("security")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Security & Privacy | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Security & Privacy</h1>
        <p class="text-muted">Account protections, login alerts, and data requests.</p>
      </div>
    {% endblock %}
    """)
