# =============================================================
# FILE: blueprints/admin/routes.py
# PittState-Connect — Admin Dashboard & Inbox Management
# Includes Inbox, Detail, Mark-as-Read, and Delete functions.
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
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.query.filter_by(is_read=False).count()
    return render_template("admin/inbox.html", messages=messages, unread_count=unread_count)

# -------------------------------------------------------------
# SINGLE MESSAGE DETAIL VIEW
# -------------------------------------------------------------
@admin_bp.route("/inbox/<int:message_id>")
@login_required
def message_detail(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("admin/message_detail.html", msg=msg)

# -------------------------------------------------------------
# MARK AS READ ACTION
# -------------------------------------------------------------
@admin_bp.route("/inbox/<int:message_id>/mark_read", methods=["POST"])
@login_required
def mark_read(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    flash("✅ Message marked as read.", "success")
    return redirect(url_for("admin_bp.inbox"))

# -------------------------------------------------------------
# DELETE MESSAGE
# -------------------------------------------------------------
@admin_bp.route("/inbox/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("🗑️ Message deleted successfully.", "info")
    return redirect(url_for("admin_bp.inbox"))
