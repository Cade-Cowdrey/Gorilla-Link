from flask import Blueprint, jsonify, render_template_string
from flask_login import login_required
from utils.security_util import require_roles
from models import db, UserAnalytics

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@analytics_bp.route("/", methods=["GET"])
@login_required
@require_roles("admin", "staff")
def index():
    total = db.session.query(UserAnalytics).count()
    html = """
    {% extends "base.html" %}
    {% block title %}Analytics · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Analytics</h1>
      <p class="mt-3 text-gray-600">Records in analytics table: <strong>{{ total }}</strong></p>
    {% endblock %}
    """
    return render_template_string(html, total=total)

@analytics_bp.route("/api", methods=["GET"])
@login_required
@require_roles("admin", "staff")
def api_summary():
    count = db.session.query(UserAnalytics).count()
    return jsonify({"count": count})
