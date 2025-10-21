from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, ActivityLog

bp = Blueprint("admin_activity", __name__, url_prefix="/admin/activity")


@bp.route("/")
@login_required
def activity_dashboard():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return render_template("admin/activity_logs.html", logs=logs)


def log_action(user_id, action, ip_address=None):
    """Utility function to record an admin or user action."""
    log = ActivityLog(user_id=user_id, action=action, ip_address=ip_address)
    db.session.add(log)
    db.session.commit()
