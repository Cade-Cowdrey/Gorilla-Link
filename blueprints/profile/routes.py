from flask import Blueprint, jsonify, render_template_string
from flask_login import login_required, current_user

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

@profile_bp.route("/", methods=["GET"])
@login_required
def index():
    html = """
    {% extends "base.html" %}
    {% block title %}Profile · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Your Profile</h1>
      <p class="mt-2 text-gray-600">Name: {{ user.first_name }} {{ user.last_name }}</p>
      <p class="text-gray-600">Email: {{ user.email }}</p>
    {% endblock %}
    """
    return render_template_string(html, user=current_user)

@profile_bp.route("/api", methods=["GET"])
@login_required
def api():
    u = current_user
    return jsonify({"id": u.id, "first_name": u.first_name, "last_name": u.last_name, "email": u.email})
