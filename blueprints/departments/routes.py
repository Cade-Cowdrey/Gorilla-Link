from flask import Blueprint, render_template
bp = Blueprint("departments_bp", __name__, url_prefix="/departments")

@bp.get("/detail")
def detail():
    return render_template("departments/detail.html")
