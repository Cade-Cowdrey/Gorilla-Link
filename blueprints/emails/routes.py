from flask import Blueprint, render_template
bp = Blueprint("emails_bp", __name__, url_prefix="/emails")

@bp.get("/confirmation-preview")
def confirmation_preview():
    return render_template("emails/confirmation.html", confirm_url="#")
