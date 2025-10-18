from flask import Blueprint, jsonify
from utils.mail_util import send_weekly_digest_students, send_weekly_digest_alumni, send_faculty_digest
from utils.security_util import require_roles
from flask_login import login_required

digests_bp = Blueprint("digests", __name__, url_prefix="/digests")

@digests_bp.route("/send/students", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def send_students():
    ok = send_weekly_digest_students()
    return jsonify({"ok": bool(ok)})

@digests_bp.route("/send/alumni", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def send_alumni():
    ok = send_weekly_digest_alumni()
    return jsonify({"ok": bool(ok)})

@digests_bp.route("/send/faculty", methods=["POST"])
@login_required
@require_roles("admin", "staff")
def send_faculty():
    ok = send_faculty_digest()
    return jsonify({"ok": bool(ok)})
