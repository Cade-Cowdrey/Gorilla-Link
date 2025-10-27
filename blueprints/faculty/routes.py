from flask import Blueprint, render_template
from utils.analytics_util import track_page_view
from flask_login import current_user

bp = Blueprint("faculty", __name__, url_prefix="/faculty")

@bp.route("/")
def faculty_home():
    track_page_view("faculty_home", current_user.id if current_user.is_authenticated else None)
    return render_template("faculty/index.html", title="Faculty | PittState-Connect")
