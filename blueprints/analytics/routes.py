from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    url_for,
    abort,
)
from flask_login import login_required
from pydantic import BaseModel, Field, ValidationError, field_validator

# -----------------------------------------------------------------------------
# Blueprint
# -----------------------------------------------------------------------------
analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/analytics",
    template_folder="../../templates/analytics",
)

# -----------------------------------------------------------------------------
# Helpers: get extensions with graceful fallbacks
# -----------------------------------------------------------------------------
def _get_socketio():
    # Expected when initialized as: socketio = SocketIO(app, ...)
    return (current_app.extensions or {}).get("socketio")

def _get_redis():
    ext = (current_app.extensions or {}).get("redis")
    if ext:
        return ext
    # Fallback to app.redis if you stored it there
    if hasattr(current_app, "redis"):
        return current_app.redis
    # Last resort: try REDIS_URL (read-only simple fallback)
    try:
        import redis  # type: ignore
        url = os.getenv("REDIS_URL")
        if url:
            return redis.from_url(url)
    except Exception:
        pass
    return None  # No Redis available

def _get_cache():
    ext = (current_app.extensions or {}).get("cache")
    if ext:
        return ext
    if hasattr(current_app, "cache"):
        return current_app.cache

    # Minimal in-memory fallback cache with interface parity (very basic)
    class _MiniCache:
        _store: Dict[str, Tuple[float, Any]] = {}

        def get(self, key: str) -> Any:
            item = self._store.get(key)
            if not item:
                return None
            exp, val = item
            if exp and exp < time.time():
                self._store.pop(key, None)
                return None
            return val

        def set(self, key: str, value: Any, timeout: int = 60) -> None:
            exp = time.time() + timeout if timeout else 0
            self._store[key] = (exp, value)

        # Flask-Caching parity used here
        def memoize(self, timeout: int = 60):
            def decorator(fn):
                def wrapper(*args, **kwargs):
                    key = f"memo:{fn.__name__}:{hashlib.sha1(repr((args, kwargs)).encode()).hexdigest()}"
                    cached = self.get(key)
                    if cached is not None:
                        return cached
                    val = fn(*args, **kwargs)
                    self.set(key, val, timeout)
                    return val
                return wrapper
            return decorator

    return _MiniCache()

def _emit(event: str, payload: Dict[str, Any], namespace: str = "/ws") -> None:
    sio = _get_socketio()
    if sio:
        try:
            sio.emit(event, payload, namespace=namespace)
        except Exception as e:
            current_app.logger.warning(f"[analytics] socketio emit failed: {e}")

# -----------------------------------------------------------------------------
# Models & Validation
# -----------------------------------------------------------------------------
class MetricsPayload(BaseModel):
    active_users: int = Field(0, ge=0)
    growth_rate: float = Field(0.0)  # percent
    total_scholarships: int = Field(0, ge=0)
    applications: int = Field(0, ge=0)
    total_donations: float = Field(0.0, ge=0.0)
    new_donors: int = Field(0, ge=0)

    @field_validator("growth_rate")
    @classmethod
    def clamp_growth(cls, v: float) -> float:
        # Prevent obviously bad inputs; allow -100..100 for completeness, then clamp to -100..500 if needed
        if v < -100.0:
            return -100.0
        if v > 500.0:
            return 500.0
        return v

# -----------------------------------------------------------------------------
# Storage keys
# -----------------------------------------------------------------------------
REDIS_METRICS_KEY = "psu:analytics:summary"
REDIS_SERIES_KEY = "psu:analytics:series"
SERIES_MAX_POINTS = 120  # last 120 ticks

# -----------------------------------------------------------------------------
# Data Access: read/write metrics & series with Redis or fallback
# -----------------------------------------------------------------------------
def _read_metrics_default() -> Dict[str, Any]:
    # Reasonable defaults if nothing is stored yet
    return {
        "active_users": 0,
        "growth_rate": 0.0,
        "total_scholarships": 0,
        "applications": 0,
        "total_donations": 0.0,
        "new_donors": 0,
        "updated_at": int(time.time()),
    }

def _read_metrics() -> Dict[str, Any]:
    r = _get_redis()
    if r:
        try:
            raw = r.get(REDIS_METRICS_KEY)
            if raw:
                return json.loads(raw)
        except Exception as e:
            current_app.logger.warning(f"[analytics] redis read failed: {e}")
    # Fallback to cached default
    return _read_metrics_default()

def _write_metrics(data: Dict[str, Any]) -> None:
    r = _get_redis()
    data["updated_at"] = int(time.time())
    if r:
        try:
            r.set(REDIS_METRICS_KEY, json.dumps(data), ex=60 * 60 * 24)  # keep a day
            return
        except Exception as e:
            current_app.logger.warning(f"[analytics] redis write failed: {e}")
    # No Redis: keep a copy in process cache for quick reads
    cache = _get_cache()
    cache.set(REDIS_METRICS_KEY, data, timeout=3600)

def _append_series_point(field: str, value: float) -> None:
    r = _get_redis()
    ts = int(time.time())
    if r:
        try:
            # store as JSON list per field
            list_key = f"{REDIS_SERIES_KEY}:{field}"
            current = r.get(list_key)
            series = json.loads(current) if current else []
            series.append([ts, value])
            series = series[-SERIES_MAX_POINTS:]
            r.set(list_key, json.dumps(series), ex=60 * 60 * 24 * 7)  # keep a week
            return
        except Exception as e:
            current_app.logger.warning(f"[analytics] series append failed: {e}")
    # Fallback: do nothing if no Redis; (optional) could store in in-memory cache

def _read_series(field: str) -> list:
    r = _get_redis()
    if r:
        try:
            list_key = f"{REDIS_SERIES_KEY}:{field}"
            current = r.get(list_key)
            series = json.loads(current) if current else []
            return series[-SERIES_MAX_POINTS:]
        except Exception as e:
            current_app.logger.warning(f"[analytics] series read failed: {e}")
    return []

# -----------------------------------------------------------------------------
# Caching decorators (use Flask-Caching if available)
# -----------------------------------------------------------------------------
_cache = _get_cache()
memoize_60 = getattr(_cache, "memoize", lambda timeout=60: (lambda f: f))(60)
memoize_300 = getattr(_cache, "memoize", lambda timeout=300: (lambda f: f))(300)

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------
@analytics_bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Renders the Analytics dashboard.
    The template can include `analytics_cards.html` partial you have.
    """
    # Render a small wrapper that pulls your cards partial
    # Create templates/analytics/index.html if you don't have one; example:
    # {% extends "base.html" %}
    # {% block title %}Analytics · PittState-Connect{% endblock %}
    # {% block content %}{% include "analytics/analytics_cards.html" %}{% endblock %}
    return render_template("index.html")


def _etag_for(obj: Any) -> str:
    try:
        raw = json.dumps(obj, sort_keys=True).encode()
    except Exception:
        raw = repr(obj).encode()
    return hashlib.sha256(raw).hexdigest()


@analytics_bp.route("/api/summary", methods=["GET"])
@login_required
def api_summary():
    """
    Cached JSON summary + strong client caching + ETag.
    """
    @memoize_60
    def _load() -> Dict[str, Any]:
        return _read_metrics()

    payload = _load()
    etag = _etag_for(payload)

    # If client sent matching ETag, return 304
    if request.headers.get("If-None-Match") == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "public, max-age=60"
        return resp

    resp = make_response(jsonify(payload), 200)
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp


@analytics_bp.route("/api/timeseries", methods=["GET"])
@login_required
def api_timeseries():
    """
    Returns time series for selected fields. Example:
      GET /analytics/api/timeseries?fields=active_users,total_donations
    """
    fields = request.args.get("fields", "active_users,total_scholarships,total_donations")
    requested = [f.strip() for f in fields.split(",") if f.strip()]
    data = {f: _read_series(f) for f in requested}
    return jsonify({"series": data, "count": {k: len(v) for k, v in data.items()}})


# -----------------------------------------------------------------------------
# Secure push endpoint (for schedulers, ETL, or admin UI) to update metrics
# -----------------------------------------------------------------------------
def _authorized_push() -> bool:
    api_key_header = request.headers.get("X-API-Key") or request.args.get("api_key")
    configured = os.getenv("ANALYTICS_PUSH_API_KEY") or current_app.config.get("ANALYTICS_PUSH_API_KEY")
    return configured and api_key_header and api_key_header == configured

@analytics_bp.route("/api/push", methods=["POST"])
def api_push():
    """
    Accepts a validated metrics payload, updates storage, appends time series,
    and emits a Socket.IO broadcast to /ws namespace.
    Protect with X-API-Key header or ?api_key=... query param.
    """
    if not _authorized_push():
        abort(401, description="Unauthorized")

    try:
        payload = MetricsPayload.model_validate(request.get_json(force=True, silent=False))
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "details": json.loads(ve.json())}), 400
    except Exception as e:
        return jsonify({"error": "bad_request", "message": str(e)}), 400

    data = payload.model_dump()
    _write_metrics(data)

    # Append each numeric to its series
    _append_series_point("active_users", float(data["active_users"]))
    _append_series_point("total_scholarships", float(data["total_scholarships"]))
    _append_series_point("total_donations", float(data["total_donations"]))

    # Emit live update
    _emit("analytics:update", data, namespace="/ws")

    return jsonify({"status": "ok", "updated": True, "at": int(time.time())}), 200


# -----------------------------------------------------------------------------
# Optional: tiny seed endpoint for local dev smoke-tests (disabled in production)
# -----------------------------------------------------------------------------
@analytics_bp.route("/dev/seed", methods=["POST"])
def dev_seed():
    """
    Quick local-only helper to seed realistic-looking metrics.
    This route automatically disables itself when FLASK_ENV=production.
    """
    env = (current_app.config.get("ENV") or os.getenv("FLASK_ENV") or "").lower()
    if env == "production":
        abort(404)

    import random

    data = {
        "active_users": random.randint(50, 500),
        "growth_rate": round(random.uniform(-5, 12), 2),
        "total_scholarships": random.randint(30, 180),
        "applications": random.randint(100, 2500),
        "total_donations": round(random.uniform(5_000, 120_000), 2),
        "new_donors": random.randint(0, 60),
    }
    _write_metrics(data)
    _append_series_point("active_users", float(data["active_users"]))
    _append_series_point("total_scholarships", float(data["total_scholarships"]))
    _append_series_point("total_donations", float(data["total_donations"]))
    _emit("analytics:update", data, namespace="/ws")
    return jsonify({"status": "seeded", "data": data})
