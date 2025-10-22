# =============================================================
# FILE: blueprints/admin/routes.py
# PittState-Connect — Admin Dashboard & Inbox Management
# Handles viewing and managing ContactMessage submissions.
# =============================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app_pro import db
from models import ContactMessage

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

# -------------------------------------------------------------
# ADMIN INBOX LIST VIEW
# -------------------------------------------------------------
@admin_bp.route("/inbox")
@login_required
def inbox():
    """Displays all messages submitted via the Contact page."""
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/inbox.html", messages=messages)

# -------------------------------------------------------------
# SINGLE MESSAGE DETAIL VIEW
# -------------------------------------------------------------
@admin_bp.route("/inbox/<int:message_id>")
@login_required
def message_detail(message_id):
    """View full content of a single message."""
    msg = ContactMessage.query.get_or_404(message_id)
    return render_template("admin/message_detail.html", msg=msg)

# -------------------------------------------------------------
# MARK AS READ / DELETE ACTIONS
# -------------------------------------------------------------
@admin_bp.route("/inbox/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    """Delete a specific message."""
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("🗑️ Message deleted successfully.", "info")
    return redirect(url_for("admin_bp.inbox"))
