# ==============================================================
# Connect API — introduces two users via email (and logs activity)
# ==============================================================
import os, smtplib, ssl
from email.mime.text import MIMEText
from flask import Blueprint, request, jsonify, abort
from flask_login import current_user, login_required
from extensions import db
from models import User, ActivityLog

bp = Blueprint("connect", __name__, url_prefix="/api/connect")

def _send_intro_email(a_email, b_email, subject, body):
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    port = int(os.getenv("MAIL_PORT", "587"))
    sender = os.getenv("MAIL_DEFAULT_SENDER", "PittState Connect <noreply@pittstate.edu>")
    if not username or not password:
        raise RuntimeError("MAIL credentials not configured")

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join([a_email, b_email])

    ctx = ssl.create_default_context()
    with smtplib.SMTP(server, port) as s:
        s.starttls(context=ctx)
        s.login(username, password)
        s.sendmail(sender, [a_email, b_email], msg.as_string())

@login_required
@bp.post("/")
def introduce():
    data = request.get_json(force=True)
    target_id = data.get("target_user_id")
    note = data.get("note", "").strip()
    if not target_id:
        abort(400, "target_user_id is required")

    me = current_user
    them = User.query.get(target_id)
    if not them:
        abort(404, "Target user not found")

    subject = "Gorilla-Link Introduction"
    body = (
        f"Hi {them.name} and {me.name},\n\n"
        f"Gorilla-Link is connecting you two to network.\n"
        f"Note from {me.name}: {note or '(no note)'}\n\n"
        "Reply-all to continue the conversation.\n\n— Pitt State Connect"
    )

    _send_intro_email(me.email, them.email, subject, body)

    db.session.add(ActivityLog(user_id=me.id, action="connect_initiated", details=f"to {them.id}"))
    db.session.commit()

    return jsonify({"ok": True})
