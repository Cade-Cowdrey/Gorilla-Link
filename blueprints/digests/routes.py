# File: blueprints/digests/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("digests", __name__, url_prefix="/digests")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="digests")

@bp.get("/")
def index():
    track_page_view("digests")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Gorilla Digest | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Gorilla Digest</h1>
        <p class="text-muted">Your personalized PSU news & alerts.</p>
      </div>
    {% endblock %}
    """)
