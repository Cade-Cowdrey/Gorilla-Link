# blueprints/api/routes.py
# ===============================================================
#  PittState-Connect API Gateway (Final, Enhanced)
#  ---------------------------------------------------------------
#  Endpoints:
#   • POST /api/ai/query
#   • POST /api/ai/tools/analyze_essay
#   • POST /api/ai/tools/optimize_resume
#   • POST /api/ai/moderate
#   • POST /api/ai/insight
#   • POST /api/ai/recommendations
#   • GET  /api/analytics/summary
#   • GET  /api/analytics/trends
#  Enhancements:
#   • RBAC decorator
#   • Redis cache (fallback to in-memory TTL)
#   • Per-IP rate limiting
#   • Activity webhook emitter
#   • Safe OpenAI call
# ===============================================================

from __future__ import annotations
import os, time, json, traceback, threading
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user

# ---------- OpenAI (optional) ----------
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai_client = None

# ---------- Redis (optional) ----------
_redis = None
try:
    import redis  # type: ignore
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        _redis = redis.from_url(redis_url)
except Exception:
    _redis = None

# ---------- In-memory fallback cache ----------
_cache_mem: dict[str, tuple[float, str]] = {}  # key -> (expires_ts, json_str)
_cache_lock = threading.Lock()

def cache_get(key: str) -> dict | None:
    if _redis:
        raw = _redis.get(key)
        if raw:
            try: return json.loads(raw)
            except Exception: return None
        return None
    with _cache_lock:
        v = _cache_mem.get(key)
        if not v: return None
        exp, data = v
        if time.time() > exp:
            _cache_mem.pop(key, None)
            return None
        try: return json.loads(data)
        except Exception: return None

def cache_set(key: str, value: dict, ttl_sec: int = 300):
    payload = json.dumps(value)
    if _redis:
        _redis.setex(key, ttl_sec, payload)
        return
    with _cache_lock:
        _cache_mem[key] = (time.time() + ttl_sec, payload)

# ---------- Simple per-IP Rate Limiter ----------
_rate_bucket: dict[str, list[float]] = {}  # ip -> timestamps (seconds)
_rate_lock = threading.Lock()
RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "60"))       # requests
RATE_WINDOW = int(os.getenv("API_RATE_WINDOW", "60"))     # seconds

def rate_limit(fn):
    @wraps(fn)
    def _wrap(*args, **kwargs):
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
        now = time.time()
        with _rate_lock:
            bucket = _rate_bucket.get(ip, [])
            # drop old
            bucket = [t for t in bucket if now - t < RATE_WINDOW]
            if len(bucket) >= RATE_LIMIT:
                return jsonify({"success": False, "error": "Too many requests"}), 429
            bucket.append(now)
            _rate_bucket[ip] = bucket
        return fn(*args, **kwargs)
    return _wrap

# ---------- RBAC Decorator ----------
def _user_roles() -> set[str]:
    # Expect your User model to have .roles (list/str) or .role
    try:
        if getattr(current_user, "is_authenticated", False):
            if hasattr(current_user, "roles") and current_user.roles:
                if isinstance(current_user.roles, (list, tuple, set)):
                    return set(map(str.lower, current_user.roles))
                return {str(current_user.roles).lower()}
            if hasattr(current_user, "role") and current_user.role:
                return {str(current_user.role).lower()}
    except Exception:
        pass
    # Fallback: header-based role (for dev/test or service calls)
    hdr = request.headers.get("X-PSU-Role")
    return {hdr.lower()} if hdr else set()

def require_roles(*allowed):
    allowed = {r.lower() for r in allowed}
    def decorator(fn):
        @wraps(fn)
        def _wrap(*args, **kwargs):
            roles = _user_roles()
            if not roles & allowed:
                return jsonify({"success": False, "error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return _wrap
    return decorator

# ---------- Safe OpenAI ----------
def safe_openai_call(prompt: str, system_prompt: str = "You are a helpful PittState assistant.", max_tokens: int = 450, temperature: float = 0.7):
    if not _openai_client:
        return {"answer": f"[Offline AI] {prompt[:140]}…"}
    try:
        resp = _openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return {"answer": resp.choices[0].message.content.strip()}
    except Exception as e:
        current_app.logger.error(f"OpenAI Error: {e}")
        return {"answer": "⚠️ AI request failed. Please try again later."}

# ---------- Webhook Emitter ----------
import urllib.request
def emit_activity(event_type: str, payload: dict):
    url = os.getenv("WEBHOOK_URL")
    if not url:
        current_app.logger.info(f"[Webhook:disabled] {event_type} {payload}")
        return
    try:
        req = urllib.request.Request(url, data=json.dumps({"type": event_type, "data": payload}).encode("utf-8"),
                                     headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as _:
            pass
        current_app.logger.info(f"[Webhook] emitted {event_type}")
    except Exception as e:
        current_app.logger.warning(f"[Webhook] failed: {e}")

# ---------- Helpers ----------
def json_ok(data: dict, **extra):
    out = {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()}
    out.update(extra)
    return jsonify(out)

def json_err(msg: str, code=400):
    return jsonify({"success": False, "error": msg}), code

# ===============================================================
#  Blueprint
# ===============================================================
api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ===============================================================
#  AI: General Query
# ===============================================================
@api_bp.route("/ai/query", methods=["POST"])
@rate_limit
def ai_query():
    data = request.get_json(silent=True) or {}
    q = (data.get("q") or "").strip()
    if not q:
        return json_err("Missing query prompt.")
    result = safe_openai_call(q)
    emit_activity("ai.query", {"q_len": len(q)})
    return json_ok(result)

# ===============================================================
#  AI: Essay Analyzer
# ===============================================================
@api_bp.route("/ai/tools/analyze_essay", methods=["POST"])
@rate_limit
def analyze_essay():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return json_err("Missing essay text.")
    prompt = (
        "You are an academic writing assistant for PittState students. "
        "Provide concise, actionable feedback with bullets, covering thesis clarity, structure, evidence, voice, and mechanics. "
        "Then propose 3 concrete revision suggestions.\n\n"
        f"Essay:\n{text}"
    )
    result = safe_openai_call(prompt, max_tokens=550)
    emit_activity("ai.essay_review", {"chars": len(text)})
    return json_ok(result)

# ===============================================================
#  AI: Résumé Optimizer
# ===============================================================
@api_bp.route("/ai/tools/optimize_resume", methods=["POST"])
@rate_limit
def optimize_resume():
    data = request.get_json(silent=True) or {}
    bullets = data.get("bullets")
    if not isinstance(bullets, list) or not bullets:
        return json_err("Invalid or missing résumé bullet points.")
    prompt = (
        "You are a career advisor for PittState-Connect. "
        "Rewrite the following résumé bullets to be concise, results-driven (use metrics), and ATS-friendly. "
        "Return as an ordered list with improved bullets only.\n\n"
        + "\n".join(f"- {b}" for b in bullets)
    )
    result = safe_openai_call(prompt, max_tokens=400)
    emit_activity("ai.resume_optimize", {"count": len(bullets)})
    return json_ok(result)

# ===============================================================
#  AI: Moderation
# ===============================================================
@api_bp.route("/ai/moderate", methods=["POST"])
@rate_limit
def moderate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return json_err("Missing text for moderation.")
    # Simple heuristic; replace with a proper model or service if needed.
    flags = any(w in text.lower() for w in ["hate", "violence", "racist", "attack", "sexual", "suicide"])
    sev = "high" if flags else "none"
    emit_activity("ai.moderate", {"flagged": flags})
    return json_ok({"flagged": flags, "severity": sev})

# ===============================================================
#  AI: Insight (Trend Summarizer)
# ===============================================================
@api_bp.route("/ai/insight", methods=["POST"])
@rate_limit
def ai_insight():
    data = request.get_json(silent=True) or {}
    context = data.get("context") or "Summarize weekly engagement and key growth metrics for PittState-Connect."
    # Optionally include current vs previous period deltas from cache
    cur = cache_get("analytics:summary") or {}
    prev = cache_get("analytics:summary:prev") or {}
    comparison = {
        "users_total": (cur.get("users_total"), prev.get("users_total")),
        "active_sessions": (cur.get("active_sessions"), prev.get("active_sessions")),
        "jobs_posted": (cur.get("jobs_posted"), prev.get("jobs_posted")),
        "events_upcoming": (cur.get("events_upcoming"), prev.get("events_upcoming")),
        "open_scholarships": (cur.get("open_scholarships"), prev.get("open_scholarships")),
        "avg_match_score": (cur.get("avg_match_score"), prev.get("avg_match_score")),
    }
    prompt = (
        "You are PittState-Connect’s analytics summarizer. "
        "Compare current vs previous period, highlight top changes with % deltas, and provide 3 action items for admins.\n\n"
        f"Context: {context}\n\n"
        f"Comparison JSON:\n{json.dumps(comparison)}"
    )
    result = safe_openai_call(prompt, max_tokens=350)
    emit_activity("ai.insight", {"with_compare": True})
    return json_ok(result)

# ===============================================================
#  AI: Smart Recommendations
# ===============================================================
@api_bp.route("/ai/recommendations", methods=["POST"])
@rate_limit
def ai_recommendations():
    data = request.get_json(silent=True) or {}
    user_profile = data.get("profile") or {}
    # In production, fetch matches from DB; here, return structured stub.
    # Example output structure for scholarships/jobs/events:
    recs = {
        "scholarships": [
            {"id": "s123", "title": "PSU Leadership Award", "score": 92},
            {"id": "s456", "title": "STEM Excellence Grant", "score": 88},
        ],
        "jobs": [
            {"id": "j111", "title": "Marketing Intern", "company": "Gorilla Media", "score": 86},
            {"id": "j222", "title": "Data Analyst Co-op", "company": "KC Tech", "score": 84},
        ],
        "events": [
            {"id": "e900", "title": "Scholarship Workshop", "when": "Wed 3 PM", "score": 80},
        ],
        "gorilla_impact_score": 78  # Gamified metric (blend of participation + completions)
    }
    emit_activity("ai.recommendations", {"profile_keys": list(user_profile.keys())})
    return json_ok(recs)

# ===============================================================
#  Analytics: Summary (Cached)
# ===============================================================
@api_bp.route("/analytics/summary", methods=["GET"])
@rate_limit
def analytics_summary():
    # Try cache first
    cached = cache_get("analytics:summary")
    if cached:
        return json_ok(cached, cached=True)

    # In production: compute from DB. Here: demo metrics.
    metrics = {
        "users_total": 4528,
        "alumni": 1679,
        "active_sessions": 118,
        "open_scholarships": 41,
        "events_upcoming": 14,
        "jobs_posted": 89,
        "avg_match_score": 88,
    }

    # rotate "previous period" once per hour as a simple demo
    if not cache_get("analytics:summary:prev") or (datetime.utcnow().minute < 5):
        cache_set("analytics:summary:prev", metrics, ttl_sec=3600)

    cache_set("analytics:summary", metrics, ttl_sec=300)  # 5 minutes
    emit_activity("analytics.summary", {"cached": False})
    return json_ok(metrics, cached=False)

# ===============================================================
#  Analytics: Trends (Cached)
# ===============================================================
@api_bp.route("/analytics/trends", methods=["GET"])
@rate_limit
def analytics_trends():
    cached = cache_get("analytics:trends")
    if cached:
        return json_ok(cached, cached=True)

    # Example weekly trend data (replace with DB aggregation)
    today = datetime.utcnow().date()
    weeks = [(today - timedelta(days=7*i)) for i in range(7)][::-1]
    series = {
        "labels": [w.strftime("%b %d") for w in weeks],
        "users":    [3800, 3925, 4010, 4150, 4275, 4410, 4528],
        "sessions": [  92,  101,   95,  108,  113,  119,  118],
        "jobs":     [  70,   72,   74,   78,   80,   85,   89],
        "events":   [  10,   11,   10,   12,   12,   13,   14],
    }
    cache_set("analytics:trends", series, ttl_sec=600)
    emit_activity("analytics.trends", {"points": len(series["labels"])})
    return json_ok(series, cached=False)

# ===============================================================
#  Admin-only Example (RBAC)
# ===============================================================
@api_bp.route("/admin/reload-cache", methods=["POST"])
@rate_limit
@require_roles("admin")
def admin_reload_cache():
    # Clear keys for demo
    try:
        if _redis:
            for key in ("analytics:summary", "analytics:trends"):
                _redis.delete(key)
        else:
            with _cache_lock:
                for key in ("analytics:summary", "analytics:trends"):
                    _cache_mem.pop(key, None)
        emit_activity("admin.reload_cache", {"by": request.headers.get("X-PSU-Role", "unknown")})
        return json_ok({"message": "Cache cleared"})
    except Exception as e:
        current_app.logger.error(f"Cache reload failed: {e}")
        return json_err("Failed to clear cache.", 500)

# ===============================================================
#  Global Error Handlers (API scope)
# ===============================================================
@api_bp.app_errorhandler(404)
def not_found(e):
    return json_err("Endpoint not found.", 404)

@api_bp.app_errorhandler(500)
def internal_error(e):
    current_app.logger.error(f"500 Error: {traceback.format_exc()}")
    return json_err("Internal server error.", 500)
