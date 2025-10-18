from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required
from utils.security_util import require_roles
from models import db, CareerBadge, UserBadge

badges_bp = Blueprint("badges", __name__, url_prefix="/badges")

@badges_bp.route("/", methods=["GET"])
def index():
    rows = CareerBadge.query.all()
    html = """
    {% extends "base.html" %}
    {% block title %}Badges · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Career Badges</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for b in rows %}<li>{{ b.name }}</li>{% else %}
          <li class="text-gray-500">No badges yet.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, rows=rows)

@badges_bp.route("/api", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def api_create():
    d = request.get_json(force=True)
    b = CareerBadge(name=d.get("name"), description=d.get("description"), icon_url=d.get("icon_url"), category=d.get("category"))
    db.session.add(b); db.session.commit()
    return jsonify({"ok": True, "id": b.id})
