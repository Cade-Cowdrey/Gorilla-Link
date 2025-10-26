# blueprints/scholarships/routes.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from flask import (
    Blueprint, render_template, request, current_app,
    redirect, url_for, flash, jsonify
)
from flask_login import login_required, current_user

# Optional shared services
try:
    from extensions import db, cache, limiter
except Exception:
    db = cache = limiter = None

# Optional models — handle absence gracefully
Scholarship = Application = SavedScholarship = EssayTemplate = None
try:
    from models import Scholarship, Application, SavedScholarship, EssayTemplate  # type: ignore
except Exception:
    pass

scholarships_bp = Blueprint("scholarships_bp", __name__, template_folder="../../templates")

# ------------- Utilities -------------
@dataclass
class Pager:
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        from math import ceil
        return max(1, ceil(self.total / self.per_page))


def _query_or_fallback(model, default: List[Dict[str, Any]], limit: int = 24) -> List[Any]:
    if model and db:
        try:
            q = model.query
            if hasattr(model, "deadline"):
                q = q.order_by(model.deadline.asc())
            elif hasattr(model, "created_at"):
                q = q.order_by(model.created_at.desc())
            return q.limit(limit).all()
        except Exception as e:
            current_app.logger.warning("[scholarships] query failed: %s", e)
    return default


def _paginate(items: List[Any], page: int, per_page: int) -> (List[Any], Pager):
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], Pager(page=page, per_page=per_page, total=total)


def cached(timeout=90, key_prefix="sch:"):
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


def rate_limited(rule: str):
    def decorator(fn):
        if not limiter:
            return fn
        return limiter.limit(rule)(fn)
    return decorator


# ------------- Routes -------------

@scholarships_bp.get("/")
@cached(timeout=180, key_prefix="sch:index:")
def index():
    """Hub landing with highlights and Smart Match entrypoint."""
    featured = _query_or_fallback(
        Scholarship,
        default=[
            {"id": 1, "name": "Gorilla Scholars Grant", "amount": 1500, "deadline": "2025-12-15"},
            {"id": 2, "name": "PSU Alumni Award", "amount": 2500, "deadline": "2025-11-30"},
        ],
        limit=8,
    )
    return render_template(
        "scholarships/index.html",
        featured=featured,
        meta={"title": "Scholarship Hub | PittState-Connect", "description": "Discover and win funding with Smart Match."},
    )


@scholarships_bp.get("/browse")
@cached(timeout=120, key_prefix="sch:browse:")
def browse():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, int(request.args.get("per_page", 12)))
    items = _query_or_fallback(
        Scholarship,
        default=[
            {"id": 101, "name": "STEM Innovators", "amount": 1000, "deadline": "2025-12-01"},
            {"id": 102, "name": "Business Leadership", "amount": 2000, "deadline": "2025-12-10"},
        ],
        limit=200,
    )
    items_page, pager = _paginate(items, page, per_page)
    return render_template(
        "scholarships/browse.html",
        items=items_page,
        pager=pager,
        meta={"title": "Browse Scholarships | PittState-Connect"},
    )


@scholarships_bp.get("/my")
@login_required
@cached(timeout=30, key_prefix="sch:my:")
def my_scholarships():
    saved = []
    applied = []
    if db and SavedScholarship and Application:
        try:
            saved = SavedScholarship.query.filter_by(user_id=current_user.id).all()
            applied = Application.query.filter_by(user_id=current_user.id).all()
        except Exception as e:
            current_app.logger.warning("[scholarships] my_scholarships query failed: %s", e)

    return render_template(
        "scholarships/my.html",
        saved=saved,
        applied=applied,
        meta={"title": "My Scholarships | PittState-Connect"},
    )


@scholarships_bp.post("/save/<int:scholarship_id>")
@login_required
@rate_limited("20/minute")
def save_scholarship(scholarship_id: int):
    if not (db and SavedScholarship):
        flash("Saving not available in this environment.", "warning")
        return redirect(url_for("scholarships_bp.browse"))
    try:
        exists = SavedScholarship.query.filter_by(
            user_id=current_user.id, scholarship_id=scholarship_id
        ).first()
        if not exists:
            rec = SavedScholarship(user_id=current_user.id, scholarship_id=scholarship_id)
            db.session.add(rec)
            db.session.commit()
        flash("Scholarship saved.", "success")
    except Exception as e:
        current_app.logger.exception("[scholarships] save failed: %s", e)
        flash("Unable to save scholarship.", "danger")
    return redirect(url_for("scholarships_bp.browse"))


@scholarships_bp.post("/apply/<int:scholarship_id>")
@login_required
@rate_limited("10/minute")
def apply(scholarship_id: int):
    if not (db and Application):
        flash("Applications are not enabled in this environment.", "warning")
        return redirect(url_for("scholarships_bp.browse"))
    try:
        payload = {
            "user_id": current_user.id,
            "scholarship_id": scholarship_id,
            "essay": request.form.get("essay", "").strip()[:20000],
        }
        rec = Application(**payload)  # type: ignore
        db.session.add(rec)
        db.session.commit()
        flash("Application submitted!", "success")
    except Exception as e:
        current_app.logger.exception("[scholarships] apply failed: %s", e)
        flash("Could not submit application.", "danger")
    return redirect(url_for("scholarships_bp.my_scholarships"))


@scholarships_bp.get("/smart-match")
@login_required
@cached(timeout=60, key_prefix="sch:smart:")
def smart_match():
    """
    Simple Smart Match recommender (placeholder logic).
    In production tie to GPA, major, department, interests, and deadlines proximity.
    """
    recommendations = _query_or_fallback(
        Scholarship,
        default=[
            {"id": 201, "name": "First-Gen Student Success", "amount": 1500, "deadline": "2025-11-20"},
            {"id": 202, "name": "Service & Leadership Award", "amount": 1200, "deadline": "2025-12-05"},
        ],
        limit=6,
    )
    return render_template(
        "scholarships/smart_match.html",
        recs=recommendations,
        meta={"title": "Smart Match | PittState-Connect"},
    )


@scholarships_bp.get("/deadlines")
@cached(timeout=300, key_prefix="sch:deadlines:")
def deadlines():
    items = _query_or_fallback(
        Scholarship,
        default=[
            {"id": 301, "name": "Engineering Excellence", "amount": 2500, "deadline": "2025-11-15"},
            {"id": 302, "name": "Health Professions", "amount": 1000, "deadline": "2025-11-18"},
        ],
        limit=100,
    )
    return render_template(
        "scholarships/deadlines.html",
        items=items,
        meta={"title": "Upcoming Deadlines | PittState-Connect"},
    )


@scholarships_bp.get("/essay-library")
@login_required
@cached(timeout=120, key_prefix="sch:essays:")
def essay_library():
    templates = _query_or_fallback(
        EssayTemplate,
        default=[
            {"id": 1, "title": "Leadership & Community Service"},
            {"id": 2, "title": "Academic Perseverance"},
        ],
        limit=50,
    )
    return render_template(
        "scholarships/essay_library.html",
        templates=templates,
        meta={"title": "Essay Library | PittState-Connect"},
    )


# -------- JSON APIs --------
@scholarships_bp.get("/api/scholarships")
def api_scholarships():
    items = _query_or_fallback(
        Scholarship,
        default=[{"id": 999, "name": "Placeholder Scholarship", "amount": 1000, "deadline": "2025-12-31"}],
        limit=100,
    )
    def to_dict(x):
        if isinstance(x, dict): return x
        fields = ("id", "name", "amount", "deadline")
        return {f: getattr(x, f, None) for f in fields}
    return jsonify([to_dict(i) for i in items])
