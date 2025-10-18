from flask import Blueprint, jsonify, render_template_string
portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/portfolio")

@portfolio_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Portfolio · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Portfolio</h1>
      <p class="mt-2 text-gray-600">Showcase your work and achievements.</p>
    {% endblock %}
    """
    return render_template_string(html)

@portfolio_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "portfolio", "ok": True})
