from flask import Blueprint, render_template, jsonify, current_app
from extensions import db, cache
from models import Department, Faculty
from utils.security_util import login_required_safe
from utils.helpers import safe_url_for
from utils.analytics_util import track_page_view
from datetime import datetime

departments_bp = Blueprint("departments_bp", __name__, url_prefix="/departments")

# ============================================================
# ✅ PRODUCTION-READY DEPARTMENTS INDEX
# ============================================================
@departments_bp.route("/", methods=["GET"])
@login_required_safe
@cache.cached(timeout=120)
def index():
    """Render department directory with analytics and PSU branding."""
    try:
        departments = db.session.execute(db.select(Department)).scalars().all()

        # Ensure every department has a slug fallback for safe linking
        for d in departments:
            if not getattr(d, "slug", None):
                d.slug = str(d.id)

        # Example analytics tracking
        track_page_view("/departments", "Departments Index")

        # PSU-branded card info (optional enrichment layer)
        department_cards = []
        for dept in departments:
            faculty_count = db.session.query(Faculty).filter(Faculty.department_id == dept.id).count()
            department_cards.append({
                "name": dept.name,
                "slug": dept.slug,
                "faculty_count": faculty_count,
                "summary": getattr(dept, "description", "Learn more about this academic department."),
                "color": "#DAA520",  # PSU gold
                "analytics_url": safe_url_for("analytics_bp.index"),
                "updated": getattr(dept, "updated_at", datetime.utcnow()).strftime("%b %d, %Y"),
            })

        current_app.logger.info("[Departments] Index loaded successfully.")

        return render_template(
            "departments/index.html",
            departments=department_cards,
            safe_url_for=safe_url_for,
        )

    except Exception as e:
        current_app.logger.error(f"[Departments] Index route error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ DEPARTMENT DETAIL VIEW
# ============================================================
@departments_bp.route("/<slug>", methods=["GET"])
@login_required_safe
def detail(slug):
    """Render a single department page with faculty list."""
    try:
        dept = db.session.scalar(db.select(Department).filter_by(slug=slug))
        if not dept:
            return render_template("errors/404.html"), 404

        faculty_members = db.session.execute(
            db.select(Faculty).filter(Faculty.department_id == dept.id)
        ).scalars().all()

        track_page_view(f"/departments/{slug}", f"Department Detail: {dept.name}")

        return render_template(
            "departments/detail.html",
            dept=dept,
            faculty=faculty_members,
            safe_url_for=safe_url_for,
        )
    except Exception as e:
        current_app.logger.error(f"[Departments] Detail route error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ API ENDPOINT (Optional Enhancement)
# ============================================================
@departments_bp.route("/api/list", methods=["GET"])
@cache.cached(timeout=180)
def api_departments():
    """Return department data as JSON for front-end integrations."""
    try:
        departments = db.session.execute(db.select(Department)).scalars().all()
        data = [
            {
                "name": d.name,
                "slug": d.slug or str(d.id),
                "faculty_count": db.session.query(Faculty).filter(Faculty.department_id == d.id).count(),
            }
            for d in departments
        ]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        current_app.logger.error(f"[Departments] API list error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
