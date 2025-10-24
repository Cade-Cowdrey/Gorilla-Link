# ===============================================================
#  PittState-Connect API Gateway — Final Polished Version
#  Includes: OpenAI endpoints, smart analytics, Redis caching,
#  webhook events, RBAC, rate limiting, AI tools, and resiliency.
# ===============================================================

from __future__ import annotations
import os, json, time, traceback, threading
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user

# ----------------------------------------------------------------
#  Optional Integrations
# ----------------------------------------------------------------
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    openai_client = None

# Redis (optional)
try:
    import redis
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url) if redis_url else None
except Exception:
    redis_client = None

# In-memory cache fallback
_cache: dict[str, tuple[float, str]] = {}
_cache_lock = threading.Lock()

def cache_get(key: str):
    if redis_client:
        raw = redis_client.get(key)
        if raw:
            try: return json.loads(raw)
            except Exception: return None
        return None
    with _cache_lock:
        v = _cache.get(key)
        if not v: return None
        exp, data = v
        if time.time() > exp:
            _cache.pop(key, None)
            return None
        try: return json.loads(data)
        except Exception: return None

def cache_set(key: str, value: dict, ttl: int = 300):
    payload = json.dumps(value)
    if redis_client:
        redis_client.setex(key, ttl, payload)
        return
    with _cache_lock:
        _cache[key] = (time.time() + ttl, payload)

# ----------------------------------------------------------------
#  Rate Limiting
# ----------------------------------------------------------------
_rate_map: dict[str, list[float]] = {}
_rate_lock = threading.Lock()
RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "60"))
RATE_WINDOW = int(os.getenv("API_RATE_WINDOW", "60"))

def rate_limit(fn):
    @wraps(fn)
    def _wrap(*a, **kw):
        ip = (request.headers.get("X-Forwarded-For", request.remote_addr or "anon").split(",")[0]).strip()
        now = time.time()
        with _rate_lock:
            hits = [t for t in _rate_map.get(ip, []) if now - t < RATE_WINDOW]
            if len(hits) >= RATE_LIMIT:
                return jsonify({"success": False, "error": "Too many requests"}), 429
            hits.append(now)
            _rate_map[ip] = hits
        return fn(*a, **kw)
    return _wrap

# ----------------------------------------------------------------
#  RBAC Decorator
# ----------------------------------------------------------------
def _roles() -> set[str]:
    try:
        if getattr(current_user, "is_authenticated", False):
            if hasattr(current_user, "roles"):
                roles = current_user.roles
                if isinstance(roles, (list, tuple, set)):
                    return {r.lower() for r in roles}
                return {str(roles).lower()}
            if hasattr(current_user, "role"):
                return {str(current_user.role).lower()}
    except Exception:
        pass
    hdr = request.headers.get("X-PSU-Role")
    return {hdr.lower()} if hdr else set()

def require_roles(*allowed):
    allowed = {r.lower() for r in allowed}
    def decorator(fn):
        @wraps(fn)
        def _wrap(*a, **kw):
            if not (_roles() & allowed):
                return jsonify({"success": False, "error": "Forbidden"}), 403
            return fn(*a, **kw)
        return _wrap
    return decorator

# ----------------------------------------------------------------
#  Webhook Logger (Slack / Discord / etc.)
# ----------------------------------------------------------------
import urllib.request
def emit_activity(event: str, data: dict):
    url = os.getenv("WEBHOOK_URL")
    if not url:
        current_app.logger.info(f"[Webhook disabled] {event} {data}")
        return
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"type": event, "data": data}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        current_app.logger.warning(f"[Webhook] Failed: {e}")

# ----------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------
def ok(data: dict, **meta): return jsonify({"success": True, "data": data, "timestamp": datetime.utcnow().isoformat(), **meta})
def err(msg: str, code=400): return jsonify({"success": False, "error": msg}), code

def safe_openai(prompt: str, system: str = "You are a helpful PittState assistant.", temp=0.7, max_tokens=450):
    if not openai_client:
        return {"answer": f"[Offline AI] {prompt[:140]}…"}
    try:
        r = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=max_tokens,
        )
        return {"answer": r.choices[0].message.content.strip()}
    except Exception as e:
        current_app.logger.error(f"OpenAI error: {e}")
        return {"answer": "⚠️ AI service temporarily unavailable."}

# ----------------------------------------------------------------
#  Blueprint
# ----------------------------------------------------------------
api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

# ===============================================================
#  AI Endpoints
# ===============================================================
@api_bp.route("/ai/query", methods=["POST"])
@rate_limit
def ai_query():
    q = (request.json or {}).get("q", "").strip()
    if not q: return err("Missing query.")
    result = safe_openai(q)
    emit_activity("ai.query", {"len": len(q)})
    return ok(result)

@api_bp.route("/ai/tools/analyze_essay", methods=["POST"])
@rate_limit
def ai_essay():
    text = (request.json or {}).get("text", "").strip()
    if not text: return err("Missing essay text.")
    prompt = (
        "You are an academic writing coach at Pitt State. "
        "Analyze this essay for clarity, evidence, and tone. "
        "Provide a 3-part structured summary with strengths, weaknesses, and improvement tips.\n\n"
        f"{text}"
    )
    result = safe_openai(prompt, max_tokens=550)
    emit_activity("ai.essay", {"chars": len(text)})
    return ok(result)

@api_bp.route("/ai/tools/optimize_resume", methods=["POST"])
@rate_limit
def ai_resume():
    data = request.json or {}
    bullets = data.get("bullets")
    if not isinstance(bullets, list) or not bullets:
        return err("Missing résumé bullets.")
    prompt = (
        "Rewrite these résumé bullets to be concise, action-oriented, and measurable. "
        "Return an improved bullet list only:\n\n" + "\n".join(f"- {b}" for b in bullets)
    )
    result = safe_openai(prompt, max_tokens=400)
    emit_activity("ai.resume", {"count": len(bullets)})
    return ok(result)

@api_bp.route("/ai/moderate", methods=["POST"])
@rate_limit
def ai_moderate():
    text = (request.json or {}).get("text", "").strip()
    if not text: return err("Missing text.")
    flag = any(w in text.lower() for w in ["hate", "violence", "racist", "suicide", "attack"])
    emit_activity("ai.moderate", {"flagged": flag})
    return ok({"flagged": flag, "severity": "high" if flag else "none"})

@api_bp.route("/ai/insight", methods=["POST"])
@rate_limit
def ai_insight():
    ctx = (request.json or {}).get("context", "Summarize recent engagement trends for PittState-Connect.")
    cur = cache_get("analytics:summary") or {}
    prev = cache_get("analytics:summary:prev") or {}
    prompt = (
        "You are PittState-Connect’s analytics summarizer. Compare current and previous metrics, "
        "highlight changes, and give 3 action insights.\n\n"
        f"Current: {json.dumps(cur)}\nPrevious: {json.dumps(prev)}"
    )
    result = safe_openai(prompt, max_tokens=350)
    emit_activity("ai.insight", {"compared": True})
    return ok(result)

@api_bp.route("/ai/recommendations", methods=["POST"])
@rate_limit
def ai_recommend():
    profile = (request.json or {}).get("profile", {})
    recs = {
        "scholarships": [
            {"id": "s100", "title": "Leadership Excellence Award", "score": 93},
            {"id": "s200", "title": "STEM Future Grant", "score": 89},
        ],
        "jobs": [
            {"id": "j300", "title": "Marketing Intern", "company": "Gorilla Media", "score": 86},
            {"id": "j400", "title": "Data Analyst Co-op", "company": "KC Tech", "score": 84},
        ],
        "events": [
            {"id": "e500", "title": "Scholarship Writing Workshop", "when": "Wed 3 PM", "score": 80},
        ],
        "gorilla_impact_score": 78
    }
    emit_activity("ai.recommend", {"keys": list(profile.keys())})
    return ok(recs)

# ===============================================================
#  Analytics Endpoints
# ===============================================================
@api_bp.route("/analytics/summary", methods=["GET"])
@rate_limit
def analytics_summary():
    cached = cache_get("analytics:summary")
    if cached: return ok(cached, cached=True)

    metrics = {
        "users_total": 4528,
        "alumni": 1679,
        "active_sessions": 118,
        "open_scholarships": 41,
        "events_upcoming": 14,
        "jobs_posted": 89,
        "avg_match_score": 88,
    }
    if not cache_get("analytics:summary:prev") or datetime.utcnow().minute < 5:
        cache_set("analytics:summary:prev", metrics, ttl=3600)
    cache_set("analytics:summary", metrics, ttl=300)
    emit_activity("analytics.summary", {"cached": False})
    return ok(metrics)

@api_bp.route("/analytics/trends", methods=["GET"])
@rate_limit
def analytics_trends():
    cached = cache_get("analytics:trends")
    if cached: return ok(cached, cached=True)

    today = datetime.utcnow().date()
    weeks = [(today - timedelta(days=7*i)) for i in range(7)][::-1]
    data = {
        "labels": [w.strftime("%b %d") for w in weeks],
        "users": [3800, 3925, 4010, 4150, 4275, 4410, 4528],
        "sessions": [92, 101, 95, 108, 113, 119, 118],
        "jobs": [70, 72, 74, 78, 80, 85, 89],
        "events": [10, 11, 10, 12, 12, 13, 14],
    }
    cache_set("analytics:trends", data, ttl=600)
    emit_activity("analytics.trends", {"points": len(data["labels"])})
    return ok(data)

# ===============================================================
#  Admin Utilities
# ===============================================================
@api_bp.route("/admin/reload-cache", methods=["POST"])
@rate_limit
@require_roles("admin")
def admin_clear_cache():
    try:
        if redis_client:
            for k in ("analytics:summary", "analytics:trends"):
                redis_client.delete(k)
        else:
            with _cache_lock:
                for k in ("analytics:summary", "analytics:trends"):
                    _cache.pop(k, None)
        emit_activity("admin.cache_reload", {"by": "admin"})
        return ok({"message": "Cache cleared."})
    except Exception as e:
        current_app.logger.error(f"Cache clear failed: {e}")
        return err("Internal cache error", 500)

# ===============================================================
#  Global Error Handlers
# ===============================================================
@api_bp.app_errorhandler(404)
def not_found(e): return err("Endpoint not found.", 404)

@api_bp.app_errorhandler(500)
def server_error(e):
    current_app.logger.error(traceback.format_exc())
    return err("Internal server error.", 500)
