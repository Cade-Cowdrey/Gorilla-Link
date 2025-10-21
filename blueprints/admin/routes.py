from flask import Blueprint, render_template
bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

@bp.get("/dashboard")
def dashboard():
    return render_template("admin/dashboard.html")
