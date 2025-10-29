# File: blueprints/community/routes.py
from flask import Blueprint, render_template_string, jsonify
from utils.analytics_util import track_page_view

bp = Blueprint("community", __name__, url_prefix="/community")

@bp.get("/health")
def health():
    return jsonify(status="ok", section="community")

@bp.get("/")
def index():
    track_page_view("community")
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}Community | PittState-Connect{% endblock %}
    {% block content %}
      <div class="container py-4">
        <h1 class="h3">Community</h1>
        <p class="text-muted">Clubs, groups, chats, and events.</p>
      </div>
    {% endblock %}
    """)
