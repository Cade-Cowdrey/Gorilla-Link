from flask import Blueprint, render_template

departments_bp = Blueprint("departments_bp", __name__, template_folder="../../templates")

@departments_bp.route("/")
def index():
    return render_template("departments/index.html")
