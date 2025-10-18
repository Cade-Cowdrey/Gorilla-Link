from flask import Blueprint, jsonify, render_template_string
map_bp = Blueprint("map", __name__, url_prefix="/map")

@map_bp.route("/", methods=["GET"])
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Map · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Campus Map</h1>
      <p class="mt-2 text-gray-600">Interactive campus map coming soon.</p>
    {% endblock %}
    """
    return render_template_string(html)

@map_bp.route("/api", methods=["GET"])
def api():
    return jsonify({"module": "map", "ok": True})
