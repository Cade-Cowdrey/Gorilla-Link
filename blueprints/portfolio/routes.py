# File: blueprints/portfolio/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("portfolio", __name__, url_prefix="/portfolio")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="portfolio")

@bp.get("/")
def index():
    track_page_view("portfolio")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Portfolios | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Student Portfolios</h1>
        <p class="text-muted">PSU-branded templates and showcases.</p>
      </div>
    {% endblock %}
    """)
