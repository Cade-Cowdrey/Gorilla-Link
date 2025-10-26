# blueprints/analytics/routes.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from flask import (
    Blueprint, render_template, request, current_app, jsonify
)
from flask_login import login_required

# Optional shared services
try:
    from extensions import cache, limiter, db
except Exception:
    cache = limiter = db = None

# Optional utils fallback
try:
    from utils.analytics_util import get_page_stats  # type: ignore
except Exception:
    def get_page_stats(page: str, days: int = 7) -> Dict[str, Any]:
        # Safe fallback if util not available
        return {"page": page, "days": days, "views": 0, "unique_users": 0, "avg_time_sec": 0}

analytics_bp = Blueprint("analytics_bp", __name__, template_folder="../../templates", url_prefix="/analytics")


# ---------- Helpers ----------
def cached(timeout=60, key_prefix="anx:"):
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


# ---------- Routes ----------

@analytics_bp.get("/")
@login_required
@cached(timeout=60, key_prefix="anx:dash:")
def dashboard():
    """
    Lightweight analytics dashboard — pageviews, uniques, avg time, and top events.
    """
    try:
        home_stats = get_page_stats("/", days=7)
        careers_stats = get_page_stats("/careers", days=7)
        sch_stats = get_page_stats("/scholarships", days=7)
    except Exception as e:
        current_app.logger.warning("[analytics] get_page_stats failed: %s", e)
        home_stats = {"page": "/", "views": 0, "unique_users": 0, "avg_time_sec": 0}
        careers_stats = {"page": "/careers", "views": 0, "unique_users": 0, "avg_time_sec": 0}
        sch_stats = {"page": "/scholarships", "views": 0, "unique_users": 0, "avg_time_sec": 0}

    cards = [
        {"title": "Home (7d)", "metrics": home_stats},
        {"title": "Careers (7d)", "metrics": careers_stats},
        {"title": "Scholarships (7d)", "metrics": sch_stats},
    ]
    return render_template(
        "analytics/dashboard.html",
        cards=cards,
        meta={"title": "Analytics | PittState-Connect"},
    )


@analytics_bp.post("/events")
@rate_limited("300/minute")
def ingest_event():
    """
    Ingest client events:
    { "type": "pageview|click|engagement", "path": "/careers", "meta": {...} }
    """
    data = request.get_json(silent=True) or {}
    if not data.get("type"):
        return jsonify(ok=False, error="Missing type"), 400
    # In real prod: write to db/redis/queue. We noop safely here.
    try:
        current_app.logger.info("[analytics] event=%s path=%s meta=%s",
                                data.get("type"), data.get("path"), data.get("meta"))
        if db:
            # Example stub table insert if you have an AnalyticsEvent model
            pass
        return jsonify(ok=True)
    except Exception as e:
        current_app.logger.exception("[analytics] ingest failed: %s", e)
        return jsonify(ok=False), 500


@analytics_bp.get("/page")
@login_required
@cached(timeout=60, key_prefix="anx:page:")
def page_summary():
    path = request.args.get("path", "/")
    days = max(1, min(30, int(request.args.get("days", 7))))
    try:
        stats = get_page_stats(path, days=days)
    except Exception as e:
        current_app.logger.warning("[analytics] summary failed: %s", e)
        stats = {"page": path, "views": 0, "unique_users": 0, "avg_time_sec": 0}
    return jsonify(stats)


@analytics_bp.get("/health")
@cached(timeout=15, key_prefix="anx:health:")
def health():
    # Quick health probe for analytics pipeline
    return jsonify(ok=True, cache=bool(cache), limiter=bool(limiter), db=bool(db)))
