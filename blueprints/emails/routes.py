from flask import Blueprint, render_template

emails_bp = Blueprint("emails_bp", __name__, template_folder="../../templates")

@emails_bp.route("/digest-preview")
def digest_preview():
    return render_template("emails/jungle_digest_email.html")
