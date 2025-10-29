# File: blueprints/ai_tools/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("ai_tools", __name__, url_prefix="/ai-tools")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="ai_tools")

@bp.get("/")
def index():
    track_page_view("ai_tools")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}AI Tools | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">AI Tools</h1>
        <p class="text-muted">Model playgrounds, résumé helpers, scholarship essay assist.</p>
      </div>
    {% endblock %}
    """)
