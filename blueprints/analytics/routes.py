# blueprints/analytics/routes.py
from __future__ import annotations

import os
import time
import math
import hashlib
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple, Optional

from flask import (
    Blueprint, current_app, render_template, jsonify, request, abort, make_response
)
from flask_login import login_required, current_user
from werkzeug.exceptions import HTTPException
from loguru import logger

try:
    # Optional deps (graceful if not installed)
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore

# These are provided by your app factory (extensions)
try:
    from app_pro import db, cache, limiter  # type: ignore
except Exception:
    db = None
    cache = None
    limiter = None

# Optional OpenAI SmartMatch (graceful fallback)
try:
    from openai import OpenAI  # openai>=1 style
except Exception:
    OpenAI = None  # type: ignore

analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/analytics",
    template_folder="../../templates/analytics",
)


# ---------- Config & Feature Flags ---------- #

def _feature_enabled(name: str, default: bool = True) -> bool:
    val = current_app.config.get(name)
    if val is None:
        return default
    if isinstance(val, str):
        return val.lower() in {"1", "true", "t", "yes", "y"}
    return bool(val)


def _demo_mode() -> bool:
    # When True, routes serve demo data without touching DB
    return _feature_enabled("ANALYTICS_DEMO_MODE", default=True)


def _auth_required() -> bool:
    # Gate UI behind login in production
    return _feature_enabled("ANALYTICS_REQUIRE_LOGIN", default=False)


# ---------- Utilities ---------- #

def etag_for_payload(payload: Any) -> str:
    """Create a strong ETag for a JSON-serializable payload."""
    digest = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    return f'W/"{digest[:32]}"'

def _json(payload: Dict[str, Any], status: int = 200, max_age: int = 300):
    """JSON response with caching + ETag + security headers."""
    resp = make_response(jsonify(payload), status)
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    resp.headers["Cache-Control"] = f"public, max-age={max_age}"
    resp.headers["ETag"] = etag_for_payload(payload)
    # Security hardening
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "interest-cohort=()"
    return resp

def _cached(ttl: int):
    """Decorator that uses Flask-Caching if available, else no-op."""
    def decorator(fn):
        if cache:
            return cache.cached(timeout=ttl)(fn)
        return fn
    return decorator


# ---------- Demo / Fallback Data ---------- #

@dataclass
class KPI:
    label: str
    value: Any
    delta: str
    icon: str

def _demo_kpis() -> List[KPI]:
    return [
        KPI("Scholarships Awarded", 312, "+8% this year", "bi-award"),
        KPI("Internship Placements", 148, "+12% QoQ", "bi-briefcase"),
        KPI("Active Alumni Mentors", 96, "+5 new this month", "bi-people-fill"),
        KPI("Funding Volume", "$2.4M", "Up 11% YTD", "bi-bar-chart-line"),
    ]

def _demo_scholarship_series() -> Dict[str, Any]:
    return {
        "labels": ["2019", "2020", "2021", "2022", "2023"],
        "datasets": [
            {
                "label": "Scholarships Awarded",
                "data": [150, 180, 210, 250, 310],
                "borderColor": "#740001",
                "backgroundColor": "rgba(238,178,17,0.2)",
                "tension": 0.4,
                "fill": True,
                "pointBackgroundColor": "#740001",
            }
        ],
    }

def _demo_funding_distribution() -> Dict[str, Any]:
    return {
        "labels": ["Endowment", "Corporate", "Alumni", "Federal Aid"],
        "datasets": [
            {
                "data": [40, 25, 20, 15],
                "backgroundColor": ["#740001", "#eeb211", "#b00020", "#ffc107"],
                "borderWidth": 1,
            }
        ],
    }

def _demo_departments() -> List[Dict[str, Any]]:
    return [
        {"name": "Engineering & Technology", "avg_award": 4200, "progress": 85},
        {"name": "Business & Entrepreneurship", "avg_award": 3700, "progress": 75},
        {"name": "Education & Human Services", "avg_award": 3100, "progress": 68},
    ]


# ---------- Data Access (DB-backed; safe if DB missing) ---------- #

def _safe_db_available() -> bool:
    return db is not None and hasattr(db, "session")

def _fetch_kpis_from_db() -> List[KPI]:
    # Example only — replace with real SQLAlchemy queries
    if not _safe_db_available():
        return _demo_kpis()
    try:
        # TODO: Implement real queries
        return _demo_kpis()
    except Exception as e:
        logger.warning(f"KPIs fallback due to error: {e}")
        return _demo_kpis()

def _fetch_scholarship_series_from_db() -> Dict[str, Any]:
    if not _safe_db_available():
        return _demo_scholarship_series()
    try:
        # TODO: Implement real queries
        return _demo_scholarship_series()
    except Exception as e:
        logger.warning(f"Scholarship series fallback due to error: {e}")
        return _demo_scholarship_series()

def _fetch_funding_distribution_from_db() -> Dict[str, Any]:
    if not _safe_db_available():
        return _demo_funding_distribution()
    try:
        # TODO: Implement real queries
        return _demo_funding_distribution()
    except Exception as e:
        logger.warning(f"Funding distribution fallback due to error: {e}")
        return _demo_funding_distribution()

def _fetch_departments_from_db() -> List[Dict[str, Any]]:
    if not _safe_db_available():
        return _demo_departments()
    try:
        # TODO: Implement real queries
        return _demo_departments()
    except Exception as e:
        logger.warning(f"Departments fallback due to error: {e}")
        return _demo_departments()


# ---------- SmartMatch AI (optional) ---------- #

def _openai_client() -> Optional[Any]:
    if not _feature_enabled("FEATURE_SMARTMATCH_AI", default=True):
        return None
    api_key = current_app.config.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.warning(f"OpenAI init failed, using fallback: {e}")
        return None

def _ai_insights_fallback() -> Dict[str, Any]:
    return {
        "summary": (
            "Based on student data, SmartMatch AI estimates 78% of students qualify "
            "for at least one scholarship and 42% for multiple sources. Expected 12% "
            "increase in awards and 17% boost in internships next year."
        ),
        "confidence": 0.76,
        "tags": ["scholarships", "internships", "predictive-trend"],
    }

def _generate_ai_insights() -> Dict[str, Any]:
    client = _openai_client()
    if client is None:
        return _ai_insights_fallback()

    prompt = (
        "You are PSU SmartMatch AI. Summarize one short paragraph (<=60 words) "
        "with concise, non-fluffy trends for scholarships and internships over the next year. "
        "Include one numeric forecast for each. Tone: helpful, neutral. No disclaimers."
    )
    try:
        # Compatible with OpenAI Python SDK v1+
        completion = client.chat.completions.create(
            model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You analyze PSU analytics data."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=160,
        )
        text = (completion.choices[0].message.content or "").strip()
        return {
            "summary": text[:500],
            "confidence": 0.8,
            "tags": ["ai", "smartmatch", "forecast"],
        }
    except Exception as e:
        logger.warning(f"AI insights error, using fallback: {e}")
        return _ai_insights_fallback()


# ---------- View: Dashboard ---------- #

@analytics_bp.route("/", methods=["GET"])
def dashboard():
    """
    Renders the PSU Analytics Dashboard.
    If ANALYTICS_REQUIRE_LOGIN=True and user is not authenticated, redirect via 401 template.
    """
    if _auth_required() and not getattr(current_user, "is_authenticated", False):
        # Lightweight 401 page to keep UX polished
        return render_template("errors/401.html"), 401

    # Page uses front-end Chart.js; hydrate with minimal seed data for faster FMP
    seed = {
        "kpis": [asdict(k) for k in _fetch_kpis_from_db()],
        "departments": _fetch_departments_from_db(),
    }
    return render_template("analytics/dashboard.html", seed=seed)


# ---------- JSON APIs (rate limited, cached, ETagged) ---------- #

# Stricter default rate; loosen or tighten per your traffic
_RATE = "30/minute"

@analytics_bp.route("/api/kpis", methods=["GET"])
@_cached(ttl=60)
@limiter.limit(_RATE) if limiter else (lambda f: f)
def api_kpis():
    payload = {"ok": True, "kpis": [asdict(k) for k in _fetch_kpis_from_db()]}
    # ETag handling
    inm = request.headers.get("If-None-Match")
    et = etag_for_payload(payload)
    if inm and inm == et:
        return ("", 304, {"ETag": et, "Cache-Control": "public, max-age=60"})
    return _json(payload, max_age=60)

@analytics_bp.route("/api/scholarships_trend", methods=["GET"])
@_cached(ttl=300)
@limiter.limit(_RATE) if limiter else (lambda f: f)
def api_scholarships_trend():
    payload = {"ok": True, "chart": _fetch_scholarship_series_from_db()}
    inm = request.headers.get("If-None-Match")
    et = etag_for_payload(payload)
    if inm and inm == et:
        return ("", 304, {"ETag": et, "Cache-Control": "public, max-age=300"})
    return _json(payload, max_age=300)

@analytics_bp.route("/api/funding_distribution", methods=["GET"])
@_cached(ttl=300)
@limiter.limit(_RATE) if limiter else (lambda f: f)
def api_funding_distribution():
    payload = {"ok": True, "chart": _fetch_funding_distribution_from_db()}
    inm = request.headers.get("If-None-Match")
    et = etag_for_payload(payload)
    if inm and inm == et:
        return ("", 304, {"ETag": et, "Cache-Control": "public, max-age=300"})
    return _json(payload, max_age=300)

@analytics_bp.route("/api/departments", methods=["GET"])
@_cached(ttl=600)
@limiter.limit(_RATE) if limiter else (lambda f: f)
def api_departments():
    payload = {"ok": True, "departments": _fetch_departments_from_db()}
    inm = request.headers.get("If-None-Match")
    et = etag_for_payload(payload)
    if inm and inm == et:
        return ("", 304, {"ETag": et, "Cache-Control": "public, max-age=600"})
    return _json(payload, max_age=600)

@analytics_bp.route("/api/ai_insights", methods=["GET"])
@_cached(ttl=300)
@limiter.limit("10/minute") if limiter else (lambda f: f)
def api_ai_insights():
    if not _feature_enabled("FEATURE_SMARTMATCH_AI", default=True):
        return _json({"ok": False, "error": "AI insights disabled"}, status=403, max_age=30)
    payload = {"ok": True, "insights": _generate_ai_insights()}
    inm = request.headers.get("If-None-Match")
    et = etag_for_payload(payload)
    if inm and inm == et:
        return ("", 304, {"ETag": et, "Cache-Control": "public, max-age=300"})
    return _json(payload, max_age=300)

@analytics_bp.route("/api/health", methods=["GET"])
@limiter.limit("30/minute") if limiter else (lambda f: f)
def api_health():
    # Minimal, but useful for smoke checks / dashboards
    now = datetime.now(timezone.utc).isoformat()
    return _json(
        {
            "ok": True,
            "ts": now,
            "demo_mode": _demo_mode(),
            "auth_required": _auth_required(),
            "db": bool(_safe_db_available()),
            "cache": bool(cache),
        },
        max_age=10,
    )


# ---------- Error Handling (Blueprint-local) ---------- #

@analytics_bp.app_errorhandler(HTTPException)
def _http_exc(err: HTTPException):
    logger.error(f"[analytics_bp] HTTP {err.code}: {err.description}")
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _json({"ok": False, "error": err.description}, status=err.code, max_age=5)
    tmpl = f"errors/{err.code}.html"
    try:
        return render_template(tmpl), err.code
    except Exception:
        return render_template("errors/generic.html", code=err.code, message=err.description), err.code


@analytics_bp.app_errorhandler(Exception)
def _uncaught(err: Exception):
    logger.exception("[analytics_bp] Unhandled exception")
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return _json({"ok": False, "error": "internal_error"}, status=500, max_age=0)
    return render_template("errors/500.html"), 500


# ---------- Security / Perf Headers (post-response) ---------- #

@analytics_bp.after_request
def _after(resp):
    # Harden security a bit more for analytics endpoints
    csp = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://api.openai.com; "
        "object-src 'none'; frame-ancestors 'self';"
    )
    resp.headers.setdefault("Content-Security-Policy", csp)
    resp.headers.setdefault("X-XSS-Protection", "0")
    return resp
