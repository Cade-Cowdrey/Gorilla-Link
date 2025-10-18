from flask import Blueprint, jsonify, render_template_string
campus_bp = Blueprint("campus", __name__, url_prefix="/campus")

@campus_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Campus · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Campus</h1>
      <p class="mt-2 text-gray-600">Campus resources and news.</p>
    {% endblock %}
    """
    return render_template_string(html)

@campus_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "campus", "ok": True})
