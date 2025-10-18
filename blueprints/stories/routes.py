from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required
from models import db, Story

stories_bp = Blueprint("stories", __name__, url_prefix="/stories")

@stories_bp.route("/", methods=["GET"])
def index():
    rows = Story.query.order_by(Story.created_at.desc()).limit(20).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Stories · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Stories</h1>
      <ul class="mt-4 list-disc pl-6">
        {% for s in rows %}<li>{{ s.title }}</li>{% else %}
          <li class="text-gray-500">No stories yet.</li>
        {% endfor %}
      </ul>
    {% endblock %}
    """
    return render_template_string(html, rows=rows)

@stories_bp.route("/api", methods=["POST"])
@login_required
def api_create():
    d = request.get_json(force=True)
    s = Story(title=d.get("title"), content=d.get("content"))
    db.session.add(s); db.session.commit()
    return jsonify({"ok": True, "id": s.id})
