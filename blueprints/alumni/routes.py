from flask import Blueprint, render_template
bp = Blueprint("alumni_bp", __name__, url_prefix="/alumni")

@bp.get("/profile")
def profile():
    return render_template("alumni/profile.html")
