from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@login_required
def dashboard():
    # placeholder stats
    stats = {
        "users": 128,
        "jobs": 52,
        "departments": 12,
        "events": 7,
    }
    return render_template("admin/dashboard.html", stats=stats)
