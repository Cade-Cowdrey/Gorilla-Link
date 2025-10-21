from flask import Blueprint, render_template
bp = Blueprint("careers_bp", __name__, url_prefix="/careers")

@bp.get("/dashboard")
def dashboard():
    return render_template("careers/dashboard.html")
