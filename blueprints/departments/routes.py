# blueprints/departments/routes.py
from flask import Blueprint, render_template
from utils.security_util import login_required_safe
from utils.analytics_util import record_page_view

bp = Blueprint("departments_bp", __name__, url_prefix="/departments")

@bp.route("/")
@login_required_safe
def department_index():
    """Display a list of departments."""
    record_page_view("departments_index")
    return render_template("departments/index.html", title="Departments | PittState-Connect")
