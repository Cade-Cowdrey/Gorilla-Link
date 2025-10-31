from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import limiter
from utils.analytics_util import record_page_view

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@limiter.limit("20/minute")
@login_required
def dashboard():
       record_page_view("admin_dashboard", current_user.id if current_user.is_authenticated else None)
    return render_template("admin/dashboard.html", title="Admin Dashboard | PittState-Connect")
