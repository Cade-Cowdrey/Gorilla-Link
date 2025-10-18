from flask import Blueprint, jsonify, request, render_template_string
from flask_login import login_required, current_user
from models import db, Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/", methods=["GET"])
@login_required
def index():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Notifications · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Notifications</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for n in items %}<li>{{ n.message }} {% if not n.read %}<span class="text-xs text-[#73000A]">(new)</span>{% endif %}</li>{% else %}
          <li class="text-gray-500">No notifications.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, items=items)

@notifications_bp.route("/api", methods=["POST"])
@login_required
def api_create():
    d = request.get_json(force=True)
    n = Notification(user_id=current_user.id, message=d.get("message", ""))
    db.session.add(n); db.session.commit()
    return jsonify({"ok": True, "id": n.id})
