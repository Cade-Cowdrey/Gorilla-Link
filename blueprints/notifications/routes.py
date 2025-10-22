from flask import Blueprint, render_template

notifications_bp = Blueprint("notifications_bp", __name__, template_folder="../../templates")

@notifications_bp.route("/settings")
def settings():
    return render_template("notifications/settings.html")
