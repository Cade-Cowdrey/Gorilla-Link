from flask import Blueprint, render_template
from flask_login import current_user
from utils.analytics_util import track_page_view

bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@bp.route("/")
def notifications_home():
    track_page_view("notifications_home", current_user.id if current_user.is_authenticated else None)
    return render_template("notifications/index.html", title="Notifications | PittState-Connect")
