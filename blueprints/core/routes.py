from flask import Blueprint, render_template, render_template_string, jsonify
core_bp = Blueprint("core", __name__, url_prefix="/core")

@core_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Core · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Core</h1>
      <p class="mt-2 text-gray-600">Welcome to the core module.</p>
    {% endblock %}
    """
    return render_template_string(html)

@core_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
