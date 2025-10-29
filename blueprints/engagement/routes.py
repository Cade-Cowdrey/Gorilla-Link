# File: blueprints/engagement/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("engagement", __name__, url_prefix="/engagement")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="engagement")

@bp.get("/")
def index():
    track_page_view("engagement")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Engagement | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Engagement</h1>
        <p class="text-muted">Campaigns, A/B tests, and conversion tracking.</p>
      </div>
    {% endblock %}
    """)
