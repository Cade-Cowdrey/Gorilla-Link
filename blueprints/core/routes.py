from flask import Blueprint, render_template
from flask_login import current_user

bp = Blueprint("core", __name__)


@bp.route("/")
def home():
    return render_template("core/home.html", user=current_user)


@bp.route("/about")
def about():
    return render_template("core/about.html")


@bp.route("/privacy")
def privacy():
    return render_template("core/privacy.html")


@bp.route("/terms")
def terms():
    return render_template("core/terms.html")
