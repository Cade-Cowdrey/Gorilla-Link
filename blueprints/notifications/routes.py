# ============================================================
# FILE: blueprints/notifications/routes.py
# ============================================================
from flask import render_template, request, redirect, url_for, flash, current_app
from . import notifications_bp

@notifications_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not current_app.config.get("NOTIFICATIONS_ENABLED", True):
        return render_template("errors/disabled.html", feature="Notifications"), 200

    if request.method == "POST":
        # TODO: persist prefs in DB
        flash("Notification preferences saved.", "success")
        return redirect(url_for("notifications_bp.settings"))

    # Safe default preferences
    prefs = {
        "scholarship_deadlines": True,
        "mentor_messages": True,
        "digest_email": True,
    }
    return render_template("notifications/settings.html", prefs=prefs)
