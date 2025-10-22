from flask import Blueprint, render_template

analytics_bp = Blueprint("analytics_bp", __name__, template_folder="../../templates")

@analytics_bp.route("/")
def dashboard():
    return render_template("analytics/dashboard.html")
