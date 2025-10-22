from flask import Blueprint, render_template

mentors_bp = Blueprint("mentors_bp", __name__, template_folder="../../templates")

@mentors_bp.route("/")
def hub():
    return render_template("mentors/hub.html")
