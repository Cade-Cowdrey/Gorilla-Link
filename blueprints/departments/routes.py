from flask import Blueprint, render_template
from utils.security_util import login_required_safe
from utils.analytics_util import track_page_view

bp = Blueprint("departments", __name__, url_prefix="/departments")

@bp.route("/")
@login_required_safe
def department_index():
    track_page_view("departments_index")
    return render_template("departments/index.html", title="Departments | PittState-Connect")
