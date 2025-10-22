# ============================================================
# FILE: blueprints/emails/routes.py
# ============================================================
from datetime import datetime
from flask import render_template, request, current_app
from . import emails_bp

@emails_bp.route("/digest-preview", methods=["GET"])
def digest_preview():
    base_url = request.url_root.rstrip("/")
    ctx = {
        "base_url": base_url,
        "current_year": datetime.utcnow().year,
    }
    # Renders standalone email HTML (no base.html extends)
    return render_template("emails/jungle_digest_email.html", **ctx)
