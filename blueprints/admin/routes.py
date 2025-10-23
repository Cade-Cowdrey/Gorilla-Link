from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__, template_folder="../../templates/admin")


# ------------------------------------------------------------
#  ADMIN ANALYTICS PORTAL
# ------------------------------------------------------------
@admin_bp.route("/admin/portal")
def portal():
    # Example static data; later tie to real DB queries
    stats = {
        "users": 3240,
        "scholarships": 148,
        "jobs": 312,
        "engagement": "82%",
        "last_updated": datetime.utcnow()
    }
    return render_template("admin/portal.html", stats=stats)


# ------------------------------------------------------------
#  SYSTEM SETTINGS
# ------------------------------------------------------------
@admin_bp.route("/admin/settings", methods=["GET", "POST"])
def settings():
    settings = {
        "site_name": "PittState-Connect",
        "support_email": "support@pittstateconnect.com",
        "maintenance_mode": False
    }
    integrations = {"sendgrid_key_masked": "••••••", "openai_key_masked": "••••••", "storage_bucket": "psu-cloud"}
    roles = {"employer_signup": True, "alumni_verify": True, "default_role": "student"}
    automation = {"digest_time": "08:00", "reminder_freq": "weekly"}

    if request.method == "POST":
        # Example of handling updates; plug into DB model later
        flash("✅ Settings saved successfully!", "success")
        return redirect(url_for("admin_bp.settings"))

    return render_template(
        "admin/settings.html",
        settings=settings,
        integrations=integrations,
        roles=roles,
        automation=automation
    )


# ------------------------------------------------------------
#  EXPORT REPORT
# ------------------------------------------------------------
@admin_bp.route("/admin/export-report")
def export_report():
    """Simulates exporting a CSV/JSON analytics report."""
    sample = {
        "timestamp": datetime.utcnow().isoformat(),
        "active_users": 3240,
        "engagement": "82%",
        "jobs_posted": 312,
    }
    return jsonify(sample)
