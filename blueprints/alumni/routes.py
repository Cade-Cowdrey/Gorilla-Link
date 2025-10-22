from flask import Blueprint, render_template

alumni_bp = Blueprint("alumni_bp", __name__, template_folder="../../templates")

@alumni_bp.route("/")
def directory():
    return render_template("alumni/directory.html")
