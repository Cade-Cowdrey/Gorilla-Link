from flask import Blueprint, render_template
bp = Blueprint("donor_bp", __name__, url_prefix="/donor")

@bp.get("/portal")
def portal():
    return render_template("donor/portal.html")
