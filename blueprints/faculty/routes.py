from flask import Blueprint, render_template, jsonify, current_app, request
from extensions import db, cache
from models import Faculty, Department
from datetime import datetime, timedelta
import random

from utils.analytics_util import track_page_view, record_profile_view
from utils.security_util import login_required_safe
from utils.helpers import safe_url_for

faculty_bp = Blueprint("faculty_bp", __name__, url_prefix="/faculty")

# ============================================================
# ✅ Faculty Directory
# ============================================================
@faculty_bp.route("/", methods=["GET"])
@login_required_safe
@cache.cached(timeout=120)
def index():
    """List all faculty members with caching and PSU styling."""
    try:
        q = request.args.get("q", "").strip().lower()
        faculty_query = db.session.execute(db.select(Faculty)).scalars().all()

        if q:
            faculty_query = [
                f for f in faculty_query
                if q in f.name.lower() or (f.department and q in f.department.name.lower())
            ]

        track_page_view("/faculty", "Faculty Directory")

        cards = [{
            "name": f.name,
            "title": f.title or "Faculty Member",
            "department": f.department.name if f.department else "Pittsburg State University",
            "slug": f.slug or str(f.id),
            "profile_image_url": getattr(f, "profile_image_url", None),
            "updated": getattr(f, "updated_at", datetime.utcnow()).strftime("%b %d, %Y"),
        } for f in faculty_query]

        return render_template("faculty/index.html", faculty=cards, safe_url_for=safe_url_for)

    except Exception as e:
        current_app.logger.error(f"[Faculty] Directory error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ Faculty Profile
# ============================================================
@faculty_bp.route("/<slug>", methods=["GET"])
@login_required_safe
def detail(slug):
    """Faculty detail view with analytics and engagement tracking."""
    try:
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return render_template("errors/404.html"), 404

        track_page_view(f"/faculty/{slug}", f"Faculty Profile: {faculty.name}")
        record_profile_view("faculty", faculty.id)

        faculty.views = getattr(faculty, "views", 0) + 1
        faculty.avg_time = getattr(faculty, "avg_time", 45)
        db.session.commit()

        return render_template("faculty/detail.html", faculty=faculty, safe_url_for=safe_url_for)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Faculty] Detail error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# ✅ Faculty Analytics (Summary)
# ============================================================
@faculty_bp.route("/api/<slug>/analytics", methods=["GET"])
@cache.cached(timeout=60)
def api_faculty_analytics(slug):
    """Returns summary analytics for faculty."""
    try:
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return jsonify({"status": "error", "message": "Faculty not found"}), 404

        data = {
            "views": getattr(faculty, "views", 0),
            "avg_time_sec": getattr(faculty, "avg_time", 0),
            "updated_at": getattr(faculty, "updated_at", datetime.utcnow()).strftime("%b %d, %Y")
        }
        return jsonify({"status": "success", "data": data})

    except Exception as e:
        current_app.logger.error(f"[Faculty] Analytics error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# ✅ Faculty Analytics (Timeseries)
# ============================================================
@faculty_bp.route("/api/<slug>/timeseries", methods=["GET"])
@cache.cached(timeout=60)
def api_faculty_timeseries(slug):
    """Returns daily view data for the last N days."""
    try:
        days = max(7, min(int(request.args.get("days", 30)), 60))
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return jsonify({"status": "error", "message": "Faculty not found"}), 404

        now = datetime.utcnow()
        rows = db.session.execute(
            db.select(FacultyDailyView).filter_by(faculty_id=faculty.id)
            .filter(FacultyDailyView.date >= now - timedelta(days=days))
            .order_by(FacultyDailyView.date.asc())
        ).scalars().all()

        # Fallback generator if no data
        if not rows:
            base = max(5, getattr(faculty, "views", 50) // 10)
            data = [{"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "views": base + random.randint(-2, 4)} for i in range(days, 0, -1)]
        else:
            data = [{"date": r.date.strftime("%Y-%m-%d"), "views": r.views} for r in rows]

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        current_app.logger.error(f"[Faculty] Timeseries API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# ✅ Faculty Search API
# ============================================================
@faculty_bp.route("/api/search", methods=["GET"])
@cache.cached(timeout=60)
def api_search():
    """Search faculty by name or department."""
    try:
        q = request.args.get("q", "").strip().lower()
        if not q:
            return jsonify({"status": "error", "message": "Missing query"}), 400

        results = []
        for f in db.session.execute(db.select(Faculty)).scalars().all():
            if q in f.name.lower() or (f.department and q in f.department.name.lower()):
                results.append({
                    "name": f.name,
                    "title": f.title,
                    "slug": f.slug,
                    "department": f.department.name if f.department else None
                })
        return jsonify({"status": "success", "count": len(results), "results": results})
    except Exception as e:
        current_app.logger.error(f"[Faculty] Search API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# ✅ DB Model for FacultyDailyView
# ============================================================
from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship

class FacultyDailyView(db.Model):
    __tablename__ = "faculty_daily_views"
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    views = Column(Integer, default=0)

    faculty = relationship("Faculty", backref="daily_views")

    def __repr__(self):
        return f"<FacultyDailyView faculty={self.faculty_id} date={self.date} views={self.views}>"
