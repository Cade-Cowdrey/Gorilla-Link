from flask import Blueprint, render_template
from utils.analytics_util import track_page_view
from flask_login import current_user

bp = Blueprint("feed", __name__, url_prefix="/feed")

@bp.route("/")
def feed_home():
    track_page_view("feed_home", current_user.id if current_user.is_authenticated else None)
    return render_template("feed/index.html", title="Feed | PittState-Connect")
