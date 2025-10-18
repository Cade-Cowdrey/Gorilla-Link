from flask import Blueprint, jsonify, render_template_string
students_bp = Blueprint("students", __name__, url_prefix="/students")

@students_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Students · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Students</h1>
      <p class="mt-2 text-gray-600">Student services and support.</p>
    {% endblock %}
    """
    return render_template_string(html)

@students_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "students", "ok": True})
