# File: blueprints/campus/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("campus", __name__, url_prefix="/campus")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="campus")

@bp.get("/")
def index():
    track_page_view("campus")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Campus | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Campus Hub</h1>
        <p class="text-muted">Maps, services, hours, and quick links.</p>
      </div>
    {% endblock %}
    """)
