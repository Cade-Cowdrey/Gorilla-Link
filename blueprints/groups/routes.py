from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models import db, Group, GroupMessage

groups_bp = Blueprint("groups", __name__, url_prefix="/groups")

@groups_bp.route("/", methods=["GET"])
@login_required
def index():
    glist = Group.query.order_by(Group.created_at.desc()).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Groups · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Groups</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for g in glist %}<li>{{ g.name }}</li>{% else %}
          <li class="text-gray-500">No groups yet.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, glist=glist)

@groups_bp.route("/api", methods=["POST"])
@login_required
def create_group():
    d = request.get_json(force=True)
    g = Group(name=d.get("name"), description=d.get("description"))
    db.session.add(g); db.session.commit()
    return jsonify({"ok": True, "id": g.id})

@groups_bp.route("/api/<int:group_id>/message", methods=["POST"])
@login_required
def send_message(group_id):
    d = request.get_json(force=True)
    m = GroupMessage(group_id=group_id, author_id=current_user.id, body=d.get("body", ""))
    db.session.add(m); db.session.commit()
    return jsonify({"ok": True, "id": m.id})
