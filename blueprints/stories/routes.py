from flask import Blueprint, render_template
from utils.analytics_util import track_page_view
from flask_login import current_user

bp = Blueprint("stories", __name__, url_prefix="/stories")

@bp.route("/")
def stories_home():
    track_page_view("stories_home", current_user.id if current_user.is_authenticated else None)
    return render_template("stories/index.html", title="Stories | PittState-Connect")
