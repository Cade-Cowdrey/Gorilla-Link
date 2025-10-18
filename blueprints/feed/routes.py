from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Post, User, Department
from datetime import datetime

feed = Blueprint("feed", __name__, template_folder="templates")


# ----------------------------------------
# 🧭 FEED HOMEPAGE
# ----------------------------------------
@feed.route("/feed")
@login_required
def feed_home():
    """
    Main social feed displaying posts from all users.
    Includes filters for departments and categories.
    """
    dept_filter = request.args.get("department")
    category_filter = request.args.get("category")

    query = Post.query.order_by(Post.created_at.desc())
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)

    posts = query.limit(50).all()
    departments = Department.query.order_by(Department.name.asc()).all()

    return render_template(
        "feed/feed.html",
        posts=posts,
        departments=departments,
        dept_filter=dept_filter,
        category_filter=category_filter,
    )


# ----------------------------------------
# ✏️ CREATE POST
# ----------------------------------------
@feed.route("/feed/create", methods=["GET", "POST"])
@login_required
def create_post():
    """Allows any verified user to create a PSU-branded post."""
    if request.method == "POST":
        content = request.form.get("content")
        department_id = request.form.get("department_id")
        category = request.form.get("category") or "general"

        if not content:
            flash("Post content cannot be empty.", "warning")
            return redirect(url_for("feed.create_post"))

        new_post = Post(
            content=content,
            department_id=department_id if department_id else None,
            user_id=current_user.id,
            category=category,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_post)
        db.session.commit()

        flash("Your post has been shared successfully! 🦍", "success")
        return redirect(url_for("feed.feed_home"))

    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template("feed/create.html", departments=departments)


# ----------------------------------------
# 💬 POST DETAIL VIEW
# ----------------------------------------
@feed.route("/feed/<int:post_id>")
@login_required
def post_detail(post_id):
    """Displays a single post with its author, comments, and metadata."""
    post = Post.query.get_or_404(post_id)
    author = User.query.get(post.user_id)
    related_posts = (
        Post.query.filter(Post.user_id == post.user_id)
        .filter(Post.id != post.id)
        .order_by(Post.created_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "feed/detail.html",
        post=post,
        author=author,
        related_posts=related_posts,
    )


# ----------------------------------------
# ❤️ LIKE / UNLIKE POST
# ----------------------------------------
@feed.route("/feed/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    """
    Toggles a like on a post.
    (In demo mode, this uses a simple counter on Post model.)
    """
    post = Post.query.get_or_404(post_id)
    if not hasattr(post, "likes"):
        post.likes = 0

    if request.form.get("action") == "unlike":
        post.likes = max(0, post.likes - 1)
    else:
        post.likes += 1

    db.session.commit()
    return jsonify({"likes": post.likes})


# ----------------------------------------
# 🗑️ DELETE POST
# ----------------------------------------
@feed.route("/feed/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    """Allows post author or admin to delete a post."""
    post = Post.query.get_or_404(post_id)
    if not getattr(current_user, "is_admin", False) and current_user.id != post.user_id:
        flash("You do not have permission to delete this post.", "danger")
        return redirect(url_for("feed.feed_home"))

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully.", "info")
    return redirect(url_for("feed.feed_home"))


# ----------------------------------------
# 🧠 USER POSTS (PROFILE FEED)
# ----------------------------------------
@feed.route("/feed/user/<int:user_id>")
@login_required
def user_feed(user_id):
    """Displays posts made by a specific user."""
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(25).all()
    return render_template("feed/user_feed.html", user=user, posts=posts)


# ----------------------------------------
# 📊 FEED ANALYTICS (JSON)
# ----------------------------------------
@feed.route("/feed/data")
@login_required
def feed_data():
    """Provides JSON data for analytics dashboards (e.g., engagement)."""
    total_posts = Post.query.count()
    most_active_user = (
        db.session.query(User.name, db.func.count(Post.id))
        .join(Post)
        .group_by(User.name)
        .order_by(db.func.count(Post.id).desc())
        .first()
    )
    posts_by_department = (
        db.session.query(Department.name, db.func.count(Post.id))
        .outerjoin(Post, Department.id == Post.department_id)
        .group_by(Department.name)
        .all()
    )

    return jsonify({
        "total_posts": total_posts,
        "most_active_user": most_active_user[0] if most_active_user else None,
        "posts_by_department": [{"department": d, "count": c} for d, c in posts_by_department],
    })


# ----------------------------------------
# 🚀 ROOT REDIRECT
# ----------------------------------------
@feed.route("/")
def feed_root_redirect():
    """Redirect /feed/ base path to main feed."""
    return redirect(url_for("feed.feed_home"))
