# File: blueprints/map/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("map", __name__, url_prefix="/map")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="map")

@bp.get("/")
def index():
    track_page_view("map")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Campus Map | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Campus Map</h1>
        <p class="text-muted">Interactive locations and routes (coming online).</p>
      </div>
    {% endblock %}
    """)
