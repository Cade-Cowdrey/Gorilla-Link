# File: blueprints/emails/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("emails", __name__, url_prefix="/emails")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="emails")

@bp.get("/")
def index():
    track_page_view("emails")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Email Center | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Email Center</h1>
        <p class="text-muted">HTML templates, notifications, and campaign logs.</p>
      </div>
    {% endblock %}
    """)
