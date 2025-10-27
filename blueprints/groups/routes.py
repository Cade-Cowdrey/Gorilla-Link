from flask import Blueprint, render_template
from utils.analytics_util import track_page_view
from flask_login import current_user

bp = Blueprint("groups", __name__, url_prefix="/groups")

@bp.route("/")
def groups_home():
    track_page_view("groups_home", current_user.id if current_user.is_authenticated else None)
    return render_template("groups/index.html", title="Groups | PittState-Connect")
