from flask import Blueprint, render_template
from extensions import limiter
from flask_login import current_user
from utils.analytics_util import track_page_view

bp = Blueprint("core", __name__)

@bp.route("/")
@limiter.limit("30/minute")
def home():
    track_page_view("home", current_user.id if current_user.is_authenticated else None)
    return render_template("core/home.html", title="Home | PittState-Connect")

@bp.route("/team")
def team():
    track_page_view("team")
    return render_template("core/team.html", title="Meet the Team | PittState-Connect")

@bp.route("/careers")
def careers():
    track_page_view("careers")
    return render_template("core/careers.html", title="Careers | PittState-Connect")
