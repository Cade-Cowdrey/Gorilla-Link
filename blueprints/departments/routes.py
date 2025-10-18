from flask import Blueprint, render_template
from models import Department
from app_pro import db

departments_bp = Blueprint("departments", __name__, url_prefix="/departments")

@departments_bp.route("/dashboard")
def dashboard():
    try:
        departments = Department.query.all()
        return render_template("departments/dashboard.html", departments=departments)
    except Exception as e:
        # Helps debug without crashing Render
        return f"<h1 style='color:red;'>Error loading departments:</h1><p>{e}</p>", 500
