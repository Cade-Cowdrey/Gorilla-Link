from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from flask import (
    Blueprint, render_template, request, current_app, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user

# Optional: use your shared db session if available
try:
    from extensions import db, cache
except Exception:
    db = cache = None

# Try importing your models. If names differ, we handle gracefully.
Job = Internship = Company = Application = SavedJob = None
try:
    # Adjust if your concrete model names differ
    from models import Job, Internship, Company, Application, SavedJob  # type: ignore
except Exception:
    pass


careers_bp = Blueprint("careers_bp", __name__, template_folder="../../templates")

# ---------- Utilities ----------

@dataclass
class Pager:
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        from math import ceil
        return max(1, ceil(self.total / self.per_page))


def _query_or_fallback(model, default: List[Dict[str, Any]]) -> List[Any]:
    """Return query results if model exists; else fallback data."""
    if model and db:
        try:
            return model.query.order_by(getattr(model, "created_at", None).desc() if hasattr(model, "created_at") else None).limit(20).all()
        except Exception as e:
            current_app.logger.warning("[careers] query failed: %s", e)
    return default


def _paginate(items: List[Any], page: int, per_page: int) -> (List[Any], Pager):
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], Pager(page=page, per_page=per_page, total=total)


# Optional caching decorator
def cached(timeout=60, key_prefix="careers:"):
    def decorator(fn):
        if not cache:
            return fn
        def wrapper(*args, **kwargs):
            key = key_prefix + request.full_path
            rv = cache.get(key)
            if rv is not None:
                return rv
            rv = fn(*args, **kwargs)
            cache.set(key, rv, timeout=timeout)
            return rv
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


# ---------- Routes ----------

@careers_bp.get("/")
@cached(timeout=120, key_prefix="careers:index:")
def index():
    """Landing page: highlight jobs, internships, and top companies."""
    featured_jobs = _query_or_fallback(
        Job,
        default=[
            {"title": "Software Engineer (PSU Alumni Preferred)", "company": "Acme Tech", "location": "Remote"},
            {"title": "Data Analyst Intern", "company": "Gorilla Analytics", "location": "Pittsburg, KS"},
        ],
    )
    featured_internships = _query_or_fallback(
        Internship,
        default=[
            {"title": "Marketing Intern", "company": "Krauss Flooring", "location": "Wichita, KS"},
        ],
    )
    top_companies = _query_or_fallback(
        Company,
        default=[
            {"name": "Krauss Flooring"},
            {"name": "Ascend Health Systems"},
            {"name": "PSU Corporate Partners"},
        ],
    )

    # Render your existing template path (you previously referenced core/careers.html)
    return render_template(
        "core/careers.html",
        featured_jobs=featured_jobs,
        featured_internships=featured_internships,
        top_companies=top_companies,
        meta={
            "title": "Careers & Internships | PittState-Connect",
            "description": "Discover jobs, internships, and employer partners aligned with PSU students and alumni.",
        },
    )


@careers_bp.get("/jobs")
@cached(timeout=60, key_prefix="careers:jobs:")
def jobs():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, int(request.args.get("per_page", 12)))

    # Fallback list if model missing
    items = _query_or_fallback(Job, default=[
        {"id": 1, "title": "Junior Backend Developer", "company": "Acme Tech", "location": "Remote"},
        {"id": 2, "title": "Territory Manager", "company": "Krauss Flooring", "location": "Kansas"},
    ])
    items_page, pager = _paginate(items, page, per_page)

    return render_template(
        "careers/jobs.html",
        items=items_page,
        pager=pager,
        meta={"title": "Jobs | PittState-Connect", "description": "Explore job opportunities for PSU community."},
    )


@careers_bp.get("/internships")
@cached(timeout=60, key_prefix="careers:internships:")
def internships():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, int(request.args.get("per_page", 12)))

    items = _query_or_fallback(Internship, default=[
        {"id": 101, "title": "Operations Intern", "company": "Krauss Flooring", "location": "Wichita, KS"},
    ])
    items_page, pager = _paginate(items, page, per_page)

    return render_template(
        "careers/internships.html",
        items=items_page,
        pager=pager,
        meta={"title": "Internships | PittState-Connect", "description": "Find internships with PSU-friendly partners."},
    )


@careers_bp.get("/companies")
@cached(timeout=120, key_prefix="careers:companies:")
def companies():
    items = _query_or_fallback(Company, default=[
        {"id": 301, "name": "Krauss Flooring"},
        {"id": 302, "name": "Cardinal Innovations"},
    ])
    return render_template(
        "careers/companies.html",
        items=items,
        meta={"title": "Companies | PittState-Connect", "description": "Browse employer partners and alumni companies."},
    )


@careers_bp.get("/jobs/<int:job_id>")
def job_detail(job_id: int):
    record = None
    if Job and db:
        try:
            record = Job.query.get(job_id)
        except Exception as e:
            current_app.logger.warning("[careers] job_detail query failed: %s", e)
    if not record:
        record = {"id": job_id, "title": "Job", "company": "Unknown", "location": "TBD", "description": "Details soon"}
    return render_template(
        "careers/job_detail.html",
        job=record,
        meta={"title": f"{getattr(record, 'title', record['title'])} | PittState-Connect"},
    )


@careers_bp.get("/internships/<int:internship_id>")
def internship_detail(internship_id: int):
    record = None
    if Internship and db:
        try:
            record = Internship.query.get(internship_id)
        except Exception as e:
            current_app.logger.warning("[careers] internship_detail query failed: %s", e)
    if not record:
        record = {"id": internship_id, "title": "Internship", "company": "Unknown", "location": "TBD", "description": "Details soon"}
    return render_template(
        "careers/internship_detail.html",
        internship=record,
        meta={"title": f"{getattr(record, 'title', record['title'])} | PittState-Connect"},
    )


# --------- Interactive actions (optional enhancements) ---------

@careers_bp.post("/jobs/<int:job_id>/save")
@login_required
def save_job(job_id: int):
    if not db or not SavedJob:
        flash("Saving not available in this environment.", "warning")
        return redirect(url_for("careers_bp.job_detail", job_id=job_id))

    try:
        exists = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()
        if not exists:
            rec = SavedJob(user_id=current_user.id, job_id=job_id)
            db.session.add(rec)
            db.session.commit()
        flash("Job saved to your list.", "success")
    except Exception as e:
        current_app.logger.exception("[careers] save_job failed: %s", e)
        flash("Could not save job at this time.", "danger")
    return redirect(url_for("careers_bp.job_detail", job_id=job_id))


@careers_bp.post("/jobs/<int:job_id>/apply")
@login_required
def apply_job(job_id: int):
    if not db or not Application:
        flash("Applications are not enabled in this environment.", "warning")
        return redirect(url_for("careers_bp.job_detail", job_id=job_id))

    try:
        payload = {
            "user_id": current_user.id,
            "job_id": job_id,
            "cover_letter": request.form.get("cover_letter", "").strip()[:10_000],
        }
        app_obj = Application(**payload)  # type: ignore
        db.session.add(app_obj)
        db.session.commit()
        flash("Application submitted successfully!", "success")
    except Exception as e:
        current_app.logger.exception("[careers] apply_job failed: %s", e)
        flash("Could not submit your application.", "danger")
    return redirect(url_for("careers_bp.job_detail", job_id=job_id))


# --------- Lightweight JSON APIs (optional) ---------

@careers_bp.get("/api/jobs")
def api_jobs():
    items = _query_or_fallback(Job, default=[
        {"id": 1, "title": "Junior Backend Developer", "company": "Acme Tech", "location": "Remote"},
    ])
    # Convert SQLAlchemy objects to dict if needed
    def to_dict(x):
        if isinstance(x, dict):
            return x
        fields = ("id", "title", "company", "location")
        out = {}
        for f in fields:
            out[f] = getattr(x, f, None)
        return out
    return jsonify([to_dict(x) for x in items])
