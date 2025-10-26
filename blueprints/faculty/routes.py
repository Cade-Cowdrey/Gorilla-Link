from flask import Blueprint, render_template, jsonify, current_app
from extensions import db, cache
from models import Faculty, Department
from utils.analytics_util import track_page_view, record_profile_view
from utils.security_util import login_required_safe
from utils.helpers import safe_url_for
from datetime import datetime

faculty_bp = Blueprint("faculty_bp", __name__, url_prefix="/faculty")

# ============================================================
# ✅ FACULTY DIRECTORY (optional enhancement)
# ============================================================
@faculty_bp.route("/", methods=["GET"])
@login_required_safe
@cache.cached(timeout=120)
def index():
    """Show all faculty members across departments."""
    try:
        faculty_members = db.session.execute(db.select(Faculty)).scalars().all()
        track_page_view("/faculty", "Faculty Directory")

        faculty_cards = []
        for f in faculty_members:
            faculty_cards.append({
                "name": f.name,
                "title": f.title or "Faculty Member",
                "department": f.department.name if f.department else "Pittsburg State University",
                "slug": f.slug or str(f.id),
                "profile_image_url": getattr(f, "profile_image_url", None),
                "updated": getattr(f, "updated_at", datetime.utcnow()).strftime("%b %d, %Y"),
            })

        return render_template(
            "faculty/index.html",
            faculty=faculty_cards,
            safe_url_for=safe_url_for,
        )

    except Exception as e:
        current_app.logger.error(f"[Faculty] Directory error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ FACULTY DETAIL VIEW (main profile page)
# ============================================================
@faculty_bp.route("/<slug>", methods=["GET"])
@login_required_safe
def detail(slug):
    """Render faculty profile with analytics integration."""
    try:
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            current_app.logger.warning(f"[Faculty] No faculty found for slug '{slug}'")
            return render_template("errors/404.html"), 404

        # Analytics tracking
        track_page_view(f"/faculty/{slug}", f"Faculty Profile: {faculty.name}")
        record_profile_view("faculty", faculty.id)

        # Dynamic fallback metrics (optional)
        faculty.views = getattr(faculty, "views", 0) + 1
        faculty.avg_time = getattr(faculty, "avg_time", 45)

        # Persist view increment
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        current_app.logger.info(f"[Faculty] Rendered profile: {faculty.name}")

        return render_template(
            "faculty/detail.html",
            faculty=faculty,
            safe_url_for=safe_url_for,
        )

    except Exception as e:
        current_app.logger.error(f"[Faculty] Detail route error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ FACULTY ANALYTICS API (optional enhancement)
# ============================================================
@faculty_bp.route("/api/<slug>/analytics", methods=["GET"])
@cache.cached(timeout=60)
def api_faculty_analytics(slug):
    """Returns faculty analytics summary as JSON."""
    try:
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return jsonify({"status": "error", "message": "Faculty not found"}), 404

        # Mock or real analytics values
        data = {
            "views": getattr(faculty, "views", 0),
            "avg_time_sec": getattr(faculty, "avg_time", 0),
            "profile_url": safe_url_for("faculty_bp.detail", slug=slug),
            "department": faculty.department.name if faculty.department else "General",
            "updated_at": getattr(faculty, "updated_at", datetime.utcnow()).strftime("%b %d, %Y"),
        }

        current_app.logger.info(f"[Faculty] Analytics API served for {faculty.name}")
        return jsonify({"status": "success", "data": data})

    except Exception as e:
        current_app.logger.error(f"[Faculty] Analytics API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# ✅ FACULTY SEARCH API (optional enhancement)
# ============================================================
@faculty_bp.route("/api/search", methods=["GET"])
@cache.cached(timeout=60)
def api_search():
    """Search faculty members by name or department."""
    from flask import request
    try:
        query = request.args.get("q", "").strip().lower()
        if not query:
            return jsonify({"status": "error", "message": "Missing search query"}), 400

        faculty_members = db.session.execute(db.select(Faculty)).scalars().all()
        results = []
        for f in faculty_members:
            if query in f.name.lower() or (f.department and query in f.department.name.lower()):
                results.append({
                    "name": f.name,
                    "title": f.title,
                    "slug": f.slug,
                    "department": f.department.name if f.department else None,
                })

        return jsonify({"status": "success", "count": len(results), "results": results})

    except Exception as e:
        current_app.logger.error(f"[Faculty] Search API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
