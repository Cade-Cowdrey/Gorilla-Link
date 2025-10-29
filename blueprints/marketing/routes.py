# File: blueprints/marketing/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("marketing", __name__, url_prefix="/marketing")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="marketing")

@bp.get("/")
def index():
    track_page_view("marketing")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Marketing | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Marketing</h1>
        <p class="text-muted">Landing pages, funnels, and sponsor assets.</p>
      </div>
    {% endblock %}
    """)
