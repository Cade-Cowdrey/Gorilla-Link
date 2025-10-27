from flask import Blueprint, render_template
from flask_login import current_user, login_required
from utils.analytics_util import track_page_view

bp = Blueprint("profile", __name__, url_prefix="/profile")

@bp.route("/")
@login_required
def profile_home():
    track_page_view("profile_home", current_user.id)
    return render_template("profile/index.html", title="Profile | PittState-Connect")
