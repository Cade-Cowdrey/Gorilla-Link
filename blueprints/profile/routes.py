from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Department, Post
from datetime import datetime
import os

profile = Blueprint("profile", __name__, template_folder="templates")

# ----------------------------------------
# 👤 VIEW USER PROFILE
# ----------------------------------------
@profile.route("/profile/<int:user_id>")
@login_required
def view_profile(user_id):
    """Public or internal profile page for any user."""
    user = User.query.get_or_404(user_id)
    department = Department.query.get(user.department_id) if user.department_id else None
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(10).all()

    return render_template(
        "profile/view.html",
        user=user,
        department=department,
        posts=posts,
    )


# ----------------------------------------
# 🧭 PERSONAL DASHBOARD (CURRENT USER)
# ----------------------------------------
@profile.route("/dashboard")
@login_required
def dashboard():
    """User dashboard showing their own stats and activities."""
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).limit(10).all()
    post_count = len(posts)
    department = Department.query.get(current_user.department_id) if current_user.department_id else None

    return render_template(
        "profile/dashboard.html",
        user=current_user,
        posts=posts,
        post_count=post_count,
        department=department,
    )


# ----------------------------------------
# ✏️ EDIT PROFILE INFO
# ----------------------------------------
@profile.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Allows users to update their profile information."""
    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name")
        bio = request.form.get("bio")
        graduation_year = request.form.get("graduation_year")
        department_id = request.form.get("department_id")

        if not name:
            flash("Name cannot be empty.", "warning")
            return redirect(url_for("profile.edit_profile"))

        current_user.name = name
        current_user.bio = bio
        current_user.graduation_year = graduation_year if graduation_year else None
        current_user.department_id = department_id if department_id else None
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.dashboard"))

    return render_template(
        "profile/edit.html",
        user=current_user,
        departments=departments,
    )


# ----------------------------------------
# 📸 UPLOAD PROFILE PICTURE
# ----------------------------------------
@profile.route("/profile/upload", methods=["POST"])
@login_required
def upload_profile_picture():
    """Handles uploading and saving of a profile image."""
    if "photo" not in request.files:
        flash("No file selected.", "warning")
        return redirect(url_for("profile.edit_profile"))

    file = request.files["photo"]
    if file.filename == "":
        flash("No file chosen.", "warning")
        return redirect(url_for("profile.edit_profile"))

    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.root_path, "static", "uploads", filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)

    current_user.profile_image = f"uploads/{filename}"
    db.session.commit()

    flash("Profile photo updated successfully!", "success")
    return redirect(url_for("profile.dashboard"))


# ----------------------------------------
# ⚙️ ACCOUNT SETTINGS PAGE
# ----------------------------------------
@profile.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Account settings for privacy and notification preferences."""
    if request.method == "POST":
        visibility = request.form.get("visibility")
        notifications = request.form.get("notifications")

        current_user.visibility = visibility or "public"
        current_user.notifications_enabled = bool(notifications)
        db.session.commit()

        flash("Settings updated successfully.", "success")
        return redirect(url_for("profile.settings"))

    return render_template("profile/settings.html", user=current_user)


# ----------------------------------------
# 🧮 PROFILE ANALYTICS DATA
# ----------------------------------------
@profile.route("/profile/data/<int:user_id>")
@login_required
def profile_data(user_id):
    """Returns JSON with engagement metrics for the given user."""
    user = User.query.get_or_404(user_id)
    total_posts = Post.query.filter_by(user_id=user.id).count()
    latest_post = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).first()
    department = Department.query.get(user.department_id).name if user.department_id else "N/A"

    return jsonify({
        "user": user.name,
        "department": department,
        "total_posts": total_posts,
        "last_active": latest_post.created_at.strftime("%b %d, %Y") if latest_post else "No posts yet"
    })


# ----------------------------------------
# 🗑️ DELETE ACCOUNT (USER SIDE)
# ----------------------------------------
@profile.route("/profile/delete", methods=["POST"])
@login_required
def delete_profile():
    """Allows a user to permanently delete their account."""
    user_name = current_user.name
    db.session.delete(current_user)
    db.session.commit()
    flash(f"Your account '{user_name}' has been permanently deleted.", "info")
    return redirect(url_for("auth.deleted"))


# ----------------------------------------
# 🚀 ROOT REDIRECT
# ----------------------------------------
@profile.route("/")
def profile_root_redirect():
    """Redirect base /profile to current user's dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("profile.dashboard"))
    return redirect(url_for("auth.login"))
