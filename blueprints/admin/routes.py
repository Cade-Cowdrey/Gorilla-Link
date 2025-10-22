# =============================================================
# FILE: blueprints/admin/routes.py
# Admin dashboard & inbox for site messages
# =============================================================

from flask import Blueprint, render_template
from flask_login import login_required
from models import ContactMessage

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

@admin_bp.route("/inbox")
@login_required
def inbox():
    """Displays all contact messages."""
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/inbox.html", messages=messages)
