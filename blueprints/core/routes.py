from flask import Blueprint, render_template
bp = Blueprint("core_bp", __name__, url_prefix="")

@bp.get("/")
def home():
    return render_template("core/home.html")

@bp.get("/events")
def events():
    return render_template("core/events.html")
