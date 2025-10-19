# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Alumni Blueprint — PSU Branded
# ---------------------------------------------------------
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Department, Post, Event

# ---------------------------------------------------------
# Blueprint Definition
# ---------------------------------------------------------
alumni_bp = Blueprint(
    "alumni_bp",
    __name__,
    url_prefix="/alumni",
    template_folder="templates"
)

# ---------------------------------------------------------
# Alumni Dashboard
# ---------------------------------------------------------
@alumni_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_authenticated:
        flash("Please log in to access alumni dashboard.", "warning")
        return redirect(url_for("auth_bp.login"))

    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    events = Event.query.order_by(Event.date.desc()).limit(5).all()

    return render_template(
        "alumni/dashboard.html",
        title="Alumni Dashboard | PittState-Connect",
        posts=posts,
        events=events,
    )

# ---------------------------------------------------------
# Alumni Directory (Networking)
# ---------------------------------------------------------
@alumni_bp.route("/directory")
@login_required
def directory():
    alumni_list = (
        User.query.filter_by(role="alumni")
        .order_by(User.last_name.asc())
        .limit(50)
        .all()
    )
    return render_template(
        "alumni/directory.html",
        title="Alumni Directory | PittState-Connect",
        alumni_list=alumni_list,
    )

# ---------------------------------------------------------
# Alumni Profile Page
# ---------------------------------------------------------
@alumni_bp.route("/profile/<int:alumni_id>")
@login_required
def profile(alumni_id):
    alumni = User.query.get_or_404(alumni_id)
    posts = Post.query.filter_by(user_id=alumni.id).all()
    return render_template(
        "alumni/profile.html",
        alumni=alumni,
        posts=posts,
        title=f"{alumni.first_name} {alumni.last_name} | Alumni Profile",
    )

# ---------------------------------------------------------
# Alumni Events
# ---------------------------------------------------------
@alumni_bp.route("/events")
@login_required
def events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template(
        "alumni/events.html",
        title="Alumni Events | PittState-Connect",
        events=events,
    )

# ---------------------------------------------------------
# Alumni Post Creation (Networking Stories)
# ---------------------------------------------------------
@alumni_bp.route("/post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        content = request.form.get("content")
        if not content:
            flash("Post content cannot be empty.", "warning")
            return redirect(url_for("alumni_bp.create_post"))

        new_post = Post(content=content, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("alumni_bp.dashboard"))

    return render_template("alumni/create_post.html", title="Create Alumni Post")

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@alumni_bp.route("/ping")
def ping():
    return "🦍 Alumni Blueprint active and healthy!"
