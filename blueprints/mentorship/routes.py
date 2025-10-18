from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models import db, Mentorship
from utils.security_util import require_roles

mentorship_bp = Blueprint("mentorship", __name__, url_prefix="/mentorship")

@mentorship_bp.route("/", methods=["GET"])
@login_required
def index():
    my = Mentorship.query.filter(
        (Mentorship.mentor_id == current_user.id) | (Mentorship.mentee_id == current_user.id)
    ).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Mentorship · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Mentorship</h1>
      <ul class="list-disc pl-6 mt-4">
        {% for m in my %}<li>#{{ m.id }} — {{ m.status }}</li>{% else %}
          <li class="text-gray-500">No mentorships yet.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, my=my)

@mentorship_bp.route("/api", methods=["POST"])
@login_required
def api_request():
    d = request.get_json(force=True)
    m = Mentorship(mentor_id=d.get("mentor_id"), mentee_id=current_user.id, status="requested")
    db.session.add(m); db.session.commit()
    return jsonify({"ok": True, "id": m.id})

@mentorship_bp.route("/api/<int:m_id>/approve", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def api_approve(m_id):
    m = Mentorship.query.get_or_404(m_id)
    m.status = "active"
    db.session.commit()
    return jsonify({"ok": True})
