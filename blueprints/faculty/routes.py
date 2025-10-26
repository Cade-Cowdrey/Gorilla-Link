from flask import Blueprint, render_template, jsonify, current_app, request
from extensions import db, cache, scheduler
from models import Faculty, Department
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
import random
from collections import defaultdict

# Utility imports
from utils.analytics_util import track_page_view, record_profile_view
from utils.security_util import login_required_safe
from utils.helpers import safe_url_for

# ============================================================
# 🔰 Blueprint Definition
# ============================================================
faculty_bp = Blueprint("faculty_bp", __name__, url_prefix="/faculty")


# ============================================================
# 🧠 Model: FacultyDailyView
# ============================================================
class FacultyDailyView(db.Model):
    __tablename__ = "faculty_daily_views"
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    views = Column(Integer, default=0)

    faculty = relationship("Faculty", backref="daily_views")

    def __repr__(self):
        return f"<FacultyDailyView faculty={self.faculty_id} date={self.date} views={self.views}>"


# ============================================================
# 🧭 Faculty Directory (Searchable)
# ============================================================
@faculty_bp.route("/", methods=["GET"])
@login_required_safe
@cache.cached(timeout=120)
def index():
    """Display faculty directory with search and PSU branding."""
    try:
        q = request.args.get("q", "").strip().lower()
        faculty_list = db.session.execute(db.select(Faculty)).scalars().all()

        if q:
            faculty_list = [
                f for f in faculty_list
                if q in f.name.lower() or (f.department and q in f.department.name.lower())
            ]

        track_page_view("/faculty", "Faculty Directory")

        faculty_cards = [{
            "name": f.name,
            "title": f.title or "Faculty Member",
            "department": f.department.name if f.department else "Pittsburg State University",
            "slug": f.slug or str(f.id),
            "profile_image_url": getattr(f, "profile_image_url", None),
            "updated": getattr(f, "updated_at", datetime.utcnow()).strftime("%b %d, %Y"),
        } for f in faculty_list]

        return render_template("faculty/index.html", faculty=faculty_cards, safe_url_for=safe_url_for)
    except Exception as e:
        current_app.logger.error(f"[Faculty] Directory error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# 👤 Faculty Profile Page
# ============================================================
@faculty_bp.route("/<slug>", methods=["GET"])
@login_required_safe
def detail(slug):
    """Faculty detail view with analytics tracking."""
    try:
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return render_template("errors/404.html"), 404

        track_page_view(f"/faculty/{slug}", f"Faculty Profile: {faculty.name}")
        record_profile_view("faculty", faculty.id)

        # Increment view count & commit
        faculty.views = getattr(faculty, "views", 0) + 1
        faculty.avg_time = getattr(faculty, "avg_time", 45)
        db.session.commit()

        return render_template("faculty/detail.html", faculty=faculty, safe_url_for=safe_url_for)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Faculty] Detail error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# 📊 Faculty Analytics Summary API
# ============================================================
@faculty_bp.route("/api/<slug>/analytics", methods=["GET"])
@cache.cached(timeout=60)
def api_faculty_analytics(slug):
    """Returns simple summary analytics for faculty."""
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
        current_app.logger.error(f"[Faculty] Analytics summary error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 📈 Faculty Analytics Timeseries API
# ============================================================
@faculty_bp.route("/api/<slug>/timeseries", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def api_faculty_timeseries(slug):
    """Returns daily view data for N days (default 30)."""
    try:
        days = max(7, min(int(request.args.get("days", 30)), 60))
        faculty = db.session.scalar(db.select(Faculty).filter_by(slug=slug))
        if not faculty:
            return jsonify({"status": "error", "message": "Faculty not found"}), 404

        now = datetime.utcnow()
        rows = db.session.execute(
            db.select(FacultyDailyView)
              .filter_by(faculty_id=faculty.id)
              .filter(FacultyDailyView.date >= now.date() - timedelta(days=days))
              .order_by(FacultyDailyView.date.asc())
        ).scalars().all()

        if not rows:
            # Fallback simulated data
            base = max(5, getattr(faculty, "views", 30) // 10)
            data = [{"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"),
                     "views": max(0, base + random.randint(-2, 4))} for i in range(days, 0, -1)]
        else:
            data = [{"date": r.date.strftime("%Y-%m-%d"), "views": r.views} for r in rows]

        return jsonify({"status": "success", "data": data})
    except Exception as e:
        current_app.logger.error(f"[Faculty] Timeseries API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 🔍 Faculty Search API
# ============================================================
@faculty_bp.route("/api/search", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
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
# 🧾 Admin Dashboard Route
# ============================================================
@faculty_bp.route("/analytics", methods=["GET"])
@login_required_safe
def admin_analytics():
    """Admin dashboard view."""
    try:
        departments = db.session.execute(db.select(Department).order_by(Department.name.asc())).scalars().all()
        dept_options = [{"name": d.name, "slug": d.slug} for d in departments if d.slug]
        return render_template("faculty/analytics.html", departments=dept_options,
                               default_days=30, safe_url_for=safe_url_for)
    except Exception as e:
        current_app.logger.error(f"[Faculty] Admin analytics render error: {e}")
        return render_template("errors/500.html"), 500


# ============================================================
# 📊 Admin API: Overview
# ============================================================
@faculty_bp.route("/api/analytics/overview", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def api_faculty_overview():
    """Overall faculty analytics for admin dashboard."""
    try:
        days = max(7, min(int(request.args.get("days", 30)), 90))
        dept_slug = request.args.get("department", "all")
        now = datetime.utcnow()
        start = now.date() - timedelta(days=days)

        fac_q = db.session.execute(db.select(Faculty)).scalars().all()
        if dept_slug != "all":
            fac_q = [f for f in fac_q if f.department and f.department.slug == dept_slug]

        ids = [f.id for f in fac_q]
        if not ids:
            return jsonify({"status": "success", "kpis": {"total_views": 0, "avg_time_sec": 0, "faculty_count": 0}, "series": []})

        rows = db.session.execute(
            db.select(FacultyDailyView)
              .filter(FacultyDailyView.faculty_id.in_(ids))
              .filter(FacultyDailyView.date >= start)
              .order_by(FacultyDailyView.date.asc())
        ).scalars().all()

        per_day = defaultdict(int)
        total_views = 0
        for r in rows:
            per_day[r.date] += r.views
            total_views += r.views

        series = [{"date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                   "views": per_day.get(start + timedelta(days=i), 0)} for i in range(days + 1)]

        avg_time = int(sum([getattr(f, "avg_time", 0) for f in fac_q]) / len(fac_q)) if fac_q else 0
        return jsonify({"status": "success",
                        "kpis": {"total_views": total_views, "avg_time_sec": avg_time, "faculty_count": len(fac_q)},
                        "series": series})
    except Exception as e:
        current_app.logger.error(f"[Faculty] Overview API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 🧩 Admin API: Department Breakdown
# ============================================================
@faculty_bp.route("/api/analytics/department-breakdown", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def api_faculty_department_breakdown():
    """Views aggregated per department."""
    try:
        days = max(7, min(int(request.args.get("days", 30)), 90))
        now = datetime.utcnow()
        start = now.date() - timedelta(days=days)
        departments = db.session.execute(db.select(Department)).scalars().all()

        labels, counts = [], []
        for d in departments:
            fids = [f.id for f in getattr(d, "faculty", [])]
            if not fids:
                continue
            rows = db.session.execute(
                db.select(FacultyDailyView)
                  .filter(FacultyDailyView.faculty_id.in_(fids))
                  .filter(FacultyDailyView.date >= start)
            ).scalars().all()
            total = sum(r.views for r in rows)
            labels.append(d.name)
            counts.append(total)

        return jsonify({"status": "success", "labels": labels, "counts": counts})
    except Exception as e:
        current_app.logger.error(f"[Faculty] Dept breakdown API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 🏆 Admin API: Top Faculty
# ============================================================
@faculty_bp.route("/api/analytics/top-faculty", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def api_faculty_top():
    """Top faculty by views for admin dashboard."""
    try:
        days = max(7, min(int(request.args.get("days", 30)), 90))
        limit = max(1, min(int(request.args.get("limit", 10)), 50))
        dept_slug = request.args.get("department", "all")

        now = datetime.utcnow()
        start = now.date() - timedelta(days=days)

        fac_q = db.session.execute(db.select(Faculty)).scalars().all()
        if dept_slug != "all":
            fac_q = [f for f in fac_q if f.department and f.department.slug == dept_slug]

        ids = [f.id for f in fac_q]
        totals = defaultdict(int)
        if ids:
            rows = db.session.execute(
                db.select(FacultyDailyView)
                  .filter(FacultyDailyView.faculty_id.in_(ids))
                  .filter(FacultyDailyView.date >= start)
            ).scalars().all()
            for r in rows:
                totals[r.faculty_id] += r.views

        faculty_by_id = {f.id: f for f in fac_q}
        items = [{"name": f.name,
                  "title": f.title or "Faculty Member",
                  "department": f.department.name if f.department else "—",
                  "slug": f.slug or str(f.id),
                  "views": totals.get(f.id, 0)} for f in fac_q]

        items.sort(key=lambda x: x["views"], reverse=True)
        return jsonify({"status": "success", "results": items[:limit]})
    except Exception as e:
        current_app.logger.error(f"[Faculty] Top faculty API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 🌙 Nightly Roll-up Job (Scheduler)
# ============================================================
@scheduler.task("cron", id="faculty_daily_rollup", hour=0, minute=5)
def nightly_faculty_rollup():
    """
    Nightly job that rolls up daily faculty view counts into FacultyDailyView.
    Runs at 12:05 AM server time.
    """
    try:
        today = datetime.utcnow().date()
        all_faculty = db.session.execute(db.select(Faculty)).scalars().all()

        for f in all_faculty:
            views_today = getattr(f, "views", 0)
            if views_today <= 0:
                continue

            record = db.session.scalar(
                db.select(FacultyDailyView)
                  .filter_by(faculty_id=f.id, date=today)
            )
            if record:
                record.views += views_today
            else:
                record = FacultyDailyView(faculty_id=f.id, date=today, views=views_today)
                db.session.add(record)

            f.views = 0  # reset daily counter

        db.session.commit()
        current_app.logger.info(f"[Scheduler] Faculty roll-up complete for {today}.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Scheduler] Faculty roll-up failed: {e}")
