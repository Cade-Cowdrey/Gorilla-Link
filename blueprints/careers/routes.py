from flask import Blueprint, render_template

careers_bp = Blueprint("careers_bp", __name__, template_folder="../../templates")

@careers_bp.route("/")
def dashboard():
    return render_template("careers/dashboard.html")
