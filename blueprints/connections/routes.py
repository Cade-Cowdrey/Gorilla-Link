from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models import db, Connection

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")

@connections_bp.route("/", methods=["GET"])
@login_required
def index():
    # Show user's pending and accepted connections
    pending = Connection.query.filter(
        ((Connection.requester_id == current_user.id) | (Connection.receiver_id == current_user.id)) &
        (Connection.status == "pending")
    ).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Connections · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Connections</h1>
      <h2 class="mt-4 font-semibold">Pending</h2>
      <ul class="list-disc pl-6">
        {% for c in pending %}<li>#{{ c.id }} — {{ c.status }}</li>{% else %}
          <li class="text-gray-500">No pending requests.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, pending=pending)

# API
@connections_bp.route("/api", methods=["POST"])
@login_required
def api_send():
    d = request.get_json(force=True)
    c = Connection(requester_id=current_user.id, receiver_id=d.get("receiver_id"), status="pending")
    db.session.add(c); db.session.commit()
    return jsonify({"ok": True, "id": c.id})

@connections_bp.route("/api/<int:c_id>/accept", methods=["POST"])
@login_required
def api_accept(c_id):
    c = Connection.query.get_or_404(c_id)
    c.status = "accepted"
    db.session.commit()
    return jsonify({"ok": True})
