from flask import Blueprint, jsonify, render_template_string
marketing_bp = Blueprint("marketing", __name__, url_prefix="/marketing")

@marketing_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Marketing · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Marketing</h1>
      <p class="mt-2 text-gray-600">Campaigns and outreach.</p>
    {% endblock %}
    """
    return render_template_string(html)

@marketing_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "marketing", "ok": True})
