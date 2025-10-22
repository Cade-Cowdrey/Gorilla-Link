from flask import Blueprint, render_template

donor_bp = Blueprint("donor_bp", __name__, template_folder="../../templates")

@donor_bp.route("/")
def portal():
    return render_template("donor/portal.html")
