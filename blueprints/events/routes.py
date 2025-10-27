from flask import Blueprint, render_template
from utils.analytics_util import track_page_view
from flask_login import current_user

bp = Blueprint("events", __name__, url_prefix="/events")

@bp.route("/")
def events_home():
    track_page_view("events_home", current_user.id if current_user.is_authenticated else None)
    return render_template("events/index.html", title="Events | PittState-Connect")
