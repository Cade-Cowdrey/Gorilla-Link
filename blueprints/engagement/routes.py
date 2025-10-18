from flask import Blueprint, jsonify, render_template_string
engagement_bp = Blueprint("engagement", __name__, url_prefix="/engagement")

@engagement_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Engagement · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Engagement</h1>
      <p class="mt-2 text-gray-600">Likes, comments, and participation metrics.</p>
    {% endblock %}
    """
    return render_template_string(html)

@engagement_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "engagement", "ok": True})
