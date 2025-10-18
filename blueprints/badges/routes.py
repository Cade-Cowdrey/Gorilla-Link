from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user
from extensions import db
from models import Badge, User, Event, Post, Department
from datetime import datetime

badges = Blueprint("badges", __name__, template_folder="templates")

# ----------------------------------------
# 🏆 USER BADGE DASHBOARD
# ----------------------------------------
@badges.route("/badges")
@login_required
def user_badges():
    """Displays PSU-branded badges earned by the current user."""
    user_badges = Badge.query.filter_by(user_id=current_user.id).order_by(Badge.awarded_at.desc()).all()
    total_badges = len(user_badges)

    return render_template(
        "badges/user_badges.html",
        badges=user_badges,
        total_badges=total_badges,
    )


# ----------------------------------------
# 🧠 ADMIN BADGE MANAGEMENT
# ----------------------------------------
@badges.route("/badges/admin")
@login_required
def admin_badges_dashboard():
    """Admin-only dashboard to review, create, and award badges."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access only.", "warning")
        return redirect(url_for("badges.user_badges"))

    all_badges = Badge.query.order_by(Badge.awarded_at.desc()).limit(100).all()
    users = User.query.order_by(User.name.asc()).all()

    return render_template(
        "badges/admin_dashboard.html",
        badges=all_badges,
        users=users,
    )


# ----------------------------------------
# 🆕 CREATE A CUSTOM BADGE
# ----------------------------------------
@badges.route("/badges/create", methods=["POST"])
@login_required
def create_badge():
    """Allows admins to create and award custom badges."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("badges.admin_badges_dashboard"))

    title = request.form.get("title")
    description = request.form.get("description")
    recipient_id = request.form.get("user_id")

    if not title or not recipient_id:
        flash("Title and recipient are required.", "warning")
        return redirect(url_for("badges.admin_badges_dashboard"))

    new_badge = Badge(
        title=title,
        description=description,
        user_id=recipient_id,
        awarded_at=datetime.utcnow(),
    )
    db.session.add(new_badge)
    db.session.commit()

    flash(f"Badge '{title}' awarded successfully!", "success")
    return redirect(url_for("badges.admin_badges_dashboard"))


# ----------------------------------------
# 🧩 AUTO-AWARD BADGES (ACTIVITY-BASED)
# ----------------------------------------
@badges.route("/badges/auto-award")
@login_required
def auto_award_badges():
    """Automatically awards badges based on user milestones."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("badges.admin_badges_dashboard"))

    users = User.query.all()
    awarded_count = 0

    for user in users:
        post_count = Post.query.filter_by(user_id=user.id).count()
        event_count = Event.query.join(Event.attendees).filter_by(id=user.id).count() if hasattr(Event, "attendees") else 0
        alumni_status = user.role == "alumni"

        # 🎓 Alumni Networker
        if alumni_status and not Badge.query.filter_by(user_id=user.id, title="Alumni Networker").first():
            db.session.add(Badge(
                title="Alumni Networker",
                description="Recognized alumni actively engaging with the PSU community.",
                user_id=user.id,
                awarded_at=datetime.utcnow(),
            ))
            awarded_count += 1

        # ✍️ Contributor
        if post_count >= 10 and not Badge.query.filter_by(user_id=user.id, title="Top Contributor").first():
            db.session.add(Badge(
                title="Top Contributor",
                description="Shared 10+ posts in the PSU feed.",
                user_id=user.id,
                awarded_at=datetime.utcnow(),
            ))
            awarded_count += 1

        # 🎟️ Event Attendee
        if event_count >= 3 and not Badge.query.filter_by(user_id=user.id, title="Event Enthusiast").first():
            db.session.add(Badge(
                title="Event Enthusiast",
                description="Participated in 3 or more campus events.",
                user_id=user.id,
                awarded_at=datetime.utcnow(),
            ))
            awarded_count += 1

    db.session.commit()
    flash(f"Auto-awarded {awarded_count} new badges!", "success")
    return redirect(url_for("badges.admin_badges_dashboard"))


# ----------------------------------------
# 📊 BADGE ANALYTICS (JSON)
# ----------------------------------------
@badges.route("/badges/data")
@login_required
def badges_data():
    """Provides JSON data for badge distribution and analytics."""
    total_badges = Badge.query.count()
    top_badges = (
        db.session.query(Badge.title, db.func.count(Badge.id))
        .group_by(Badge.title)
        .order_by(db.func.count(Badge.id).desc())
        .limit(10)
        .all()
    )
    badge_data = [{"title": t, "count": c} for t, c in top_badges]

    return jsonify({
        "total_badges": total_badges,
        "popular_badges": badge_data
    })


# ----------------------------------------
# 🗑️ DELETE A BADGE
# ----------------------------------------
@badges.route("/badges/delete/<int:badge_id>", methods=["POST"])
@login_required
def delete_badge(badge_id):
    """Allows admins to delete a badge record."""
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for("badges.admin_badges_dashboard"))

    badge = Badge.query.get_or_404(badge_id)
    db.session.delete(badge)
    db.session.commit()

    flash(f"Badge '{badge.title}' deleted successfully.", "info")
    return redirect(url_for("badges.admin_badges_dashboard"))


# ----------------------------------------
# 🚀 ROOT REDIRECT
# ----------------------------------------
@badges.route("/")
def badges_root_redirect():
    """Redirect base /badges path to user dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("badges.user_badges"))
    return redirect(url_for("auth.login"))
