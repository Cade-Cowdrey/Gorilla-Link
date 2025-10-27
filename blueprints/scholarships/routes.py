from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.analytics_util import track_page_view

bp = Blueprint("scholarships", __name__, url_prefix="/scholarships")

@bp.route("/")
@login_required
def scholarships_home():
    track_page_view("scholarships_home", current_user.id)
    return render_template("scholarships/index.html", title="Scholarships | PittState-Connect")
