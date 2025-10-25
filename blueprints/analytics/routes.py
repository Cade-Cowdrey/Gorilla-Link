from flask import Blueprint, request, render_template, send_file, jsonify, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime
from io import BytesIO
from utils.report_pdf import build_monthly_report_pdf
from utils.mail_util import send_monthly_report_pdf
from utils.analytics_util import run_usage_analytics
from app_pro import db
import matplotlib.pyplot as plt
import base64
import io

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

# --- Role enforcement --------------------------------------------------------
def _require_admin():
    if not (getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"):
        abort(403, "Admin access required.")


# --- Chart Generator ---------------------------------------------------------
def generate_usage_chart(time_series):
    """Generates base64 PNG line chart for user/posts trends."""
    if not time_series:
        return None
    try:
        dates = [x["date"] for x in time_series]
        users = [x["users"] for x in time_series]
        posts = [x["posts"] for x in time_series]

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(dates, users, label="Users", linewidth=2)
        ax.plot(dates, posts, label="Posts", linewidth=2, linestyle="--")
        ax.set_title("Monthly Engagement Trend", fontsize=10)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        img_buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(img_buf, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        img_buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(img_buf.read()).decode('utf-8')}"
    except Exception as e:
        current_app.logger.warning(f"[Chart] Generation failed: {e}")
        return None


# --- Analytics Dashboard -----------------------------------------------------
@analytics_bp.route("/dashboard")
@login_required
def dashboard():
    """Show summarized analytics with charts."""
    _require_admin()
    metrics = run_usage_analytics(db)
    metrics["chart_img_base64"] = generate_usage_chart(metrics.get("time_series", []))
    return render_template("analytics/insights_dashboard.html", metrics=metrics)


# --- PDF Preview -------------------------------------------------------------
@analytics_bp.route("/reports/monthly/preview")
@login_required
def monthly_preview():
    _require_admin()
    month = int(request.args.get("month", datetime.utcnow().month))
    year = int(request.args.get("year", datetime.utcnow().year))
    department_id = request.args.get("department_id", type=int)

    metrics = run_usage_analytics(db, month=month, year=year, department_id=department_id)
    metrics["chart_img_base64"] = generate_usage_chart(metrics.get("time_series", []))
    return render_template(
        "reports/monthly_report.html",
        period_label=f"{datetime(year, month, 1):%B %Y}",
        generated_at=datetime.utcnow().strftime("%B %d, %Y %H:%M UTC"),
        department_id=department_id,
        metrics=metrics,
        ai_summary="Preview mode: AI narrative will appear in exported PDF."
    )


# --- PDF Download ------------------------------------------------------------
@analytics_bp.route("/reports/monthly.pdf")
@login_required
def monthly_pdf():
    _require_admin()
    month = int(request.args.get("month", datetime.utcnow().month))
    year = int(request.args.get("year", datetime.utcnow().year))
    department_id = request.args.get("department_id", type=int)
    filename, pdf_bytes, _ = build_monthly_report_pdf(db, month, year, department_id)
    return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=filename, mimetype="application/pdf")


# --- Email PDF ---------------------------------------------------------------
@analytics_bp.route("/reports/monthly/email", methods=["POST"])
@login_required
def monthly_email():
    _require_admin()
    month = int(request.form.get("month", datetime.utcnow().month))
    year = int(request.form.get("year", datetime.utcnow().year))
    department_id = request.form.get("department_id", type=int)
    recipients = request.form.getlist("recipients") or ["admin@pittstate.edu"]
    ok = send_monthly_report_pdf(recipients, month, year, department_id)
    return jsonify({"ok": ok})
