from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required
from utils.security_util import require_roles
from models import db, Event

events_bp = Blueprint("events", __name__, url_prefix="/events")

@events_bp.route("/", methods=["GET"])
def index():
    rows = Event.query.order_by(Event.start_time.asc()).limit(25).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Events · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Events</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for e in rows %}<li>{{ e.title }} — {{ e.location or 'TBA' }}</li>{% else %}
          <li class="text-gray-500">No upcoming events.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, rows=rows)

@events_bp.route("/api", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def api_create():
    d = request.get_json(force=True)
    e = Event(title=d.get("title"), description=d.get("description"), location=d.get("location"))
    db.session.add(e); db.session.commit()
    return jsonify({"ok": True, "id": e.id})
