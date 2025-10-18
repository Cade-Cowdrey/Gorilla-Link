from flask import Blueprint, jsonify
from flask_login import login_required
from utils.security_util import require_roles
from utils.mail_util import build_weekly_digest_data

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/", methods=["GET"])
@login_required
@require_roles("admin", "staff")
def index():
    data = build_weekly_digest_data(audience="students")
    return jsonify({"ok": True, "digest_preview": data})
