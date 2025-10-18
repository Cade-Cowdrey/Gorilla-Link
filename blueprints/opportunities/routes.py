from flask import Blueprint, jsonify, render_template_string
opportunities_bp = Blueprint("opportunities", __name__, url_prefix="/opportunities")

@opportunities_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Opportunities · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Opportunities</h1>
      <p class="mt-2 text-gray-600">Scholarships, projects, and more.</p>
    {% endblock %}
    """
    return render_template_string(html)

@opportunities_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "opportunities", "ok": True})
