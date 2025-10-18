from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required
from models import db, Alumni, User
from utils.security_util import require_roles

alumni_bp = Blueprint("alumni", __name__, url_prefix="/alumni")

@alumni_bp.route("/", methods=["GET"])
def index():
    rows = Alumni.query.limit(25).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Alumni · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Alumni Network</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for a in rows %}
          <li>{{ a.company or '—' }} — {{ a.current_position or '—' }}</li>
        {% else %}
          <li class="text-gray-500">No alumni profiles yet.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, rows=rows)

@alumni_bp.route("/api", methods=["GET"])
def api_list():
    rows = Alumni.query.all()
    return jsonify([{
        "id": a.id, "user_id": a.user_id, "year": a.graduation_year,
        "major": a.major, "company": a.company, "position": a.current_position
    } for a in rows])

@alumni_bp.route("/api", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def api_create():
    d = request.get_json(force=True)
    a = Alumni(
        user_id=d.get("user_id"),
        graduation_year=d.get("graduation_year"),
        major=d.get("major"),
        current_position=d.get("current_position"),
        company=d.get("company"),
        location=d.get("location"),
        linkedin_url=d.get("linkedin_url"),
        verified=bool(d.get("verified", False)),
    )
    db.session.add(a); db.session.commit()
    return jsonify({"ok": True, "id": a.id})
