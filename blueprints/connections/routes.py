from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.analytics_util import track_page_view

bp = Blueprint("connections", __name__, url_prefix="/connections")

@bp.route("/")
@login_required
def connections_home():
    track_page_view("connections_home", current_user.id)
    return render_template("connections/index.html", title="Connections | PittState-Connect")
