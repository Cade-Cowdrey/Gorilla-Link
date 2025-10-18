from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models import db, Post
from utils.security_util import require_roles

feed_bp = Blueprint("feed", __name__, url_prefix="/feed")

@feed_bp.route("/", methods=["GET"])
@login_required
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(25).all()
    html = """
    {% extends "base.html" %}
    {% block title %}Feed · PittState{% endblock %}
    {% block content %}
      <h1 class="text-2xl font-bold text-[#73000A]">Campus Feed</h1>
      <div class="mt-6 space-y-4">
        {% for p in posts %}
          <article class="bg-white dark:bg-[#1b1b1b] rounded-xl p-4 shadow">
            <div class="text-sm text-gray-500">{{ p.created_at.strftime('%b %d, %Y %I:%M %p') }}</div>
            <p class="mt-2">{{ p.content }}</p>
          </article>
        {% else %}
          <p class="text-gray-500">No posts yet.</p>
        {% endfor %}
      </div>
      <form class="mt-6" method="post" action="{{ url_for('feed.create_post') }}">
        <textarea name="content" class="w-full p-3 rounded border" rows="3" placeholder="Share something..."></textarea>
        <button class="mt-2 bg-[#FFD700] text-[#73000A] px-4 py-2 rounded font-semibold">Post</button>
      </form>
    {% endblock %}
    """
    return render_template_string(html, posts=posts)

@feed_bp.route("/create", methods=["POST"])
@login_required
def create_post():
    content = (request.form.get("content") or request.json.get("content") if request.is_json else "").strip()
    if not content:
        return jsonify({"ok": False, "error": "content required"}), 400
    post = Post(user_id=current_user.id, content=content)
    db.session.add(post)
    db.session.commit()
    return jsonify({"ok": True, "id": post.id})

# API
@feed_bp.route("/api", methods=["GET"])
def api_list():
    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()
    return jsonify([{"id": p.id, "user_id": p.user_id, "content": p.content, "created_at": p.created_at.isoformat()} for p in posts])

@feed_bp.route("/api", methods=["POST"])
@login_required
def api_create():
    data = request.get_json(force=True)
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "content required"}), 400
    p = Post(user_id=current_user.id, content=content)
    db.session.add(p); db.session.commit()
    return jsonify({"ok": True, "id": p.id})
