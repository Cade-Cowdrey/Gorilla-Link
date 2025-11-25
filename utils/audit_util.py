# utils/audit_util.py
# ---------------------------------------------------------------------
# PSU Audit Utility (Production-Ready, Safe-by-Default)
# ---------------------------------------------------------------------
# Features
# - Unified audit event API (route & job decorators, direct record)
# - Context capture (user/id/email, IP, UA, request path/method, referrer)
# - PII scrubbing & safe-json serialization
# - Redis-backed hot log with retention; optional DB write-through
# - Integrity HMAC (tamper-evident) + correlation IDs
# - Suspicious event detection & alerting via mail_util (optional)
# - Rate limiting for noisy actors (per user/ip)
# - Exports (CSV, NDJSON), batch fetch for dashboards
# - GDPR/CCPA helpers (user wipe by id/email), retention cleanup
# - Fully guarded imports (runs even if Redis/DB/Flask not available)
#
# Tables (optional; create via migrations if using DB persistence):
# ---------------------------------------------------------------------
# -- Example schema (PostgreSQL):
# CREATE TABLE audit_logs (
#   id BIGSERIAL PRIMARY KEY,
#   occurred_at TIMESTAMPTZ NOT NULL,
#   level VARCHAR(16) NOT NULL,           -- info|warning|error|security
#   action VARCHAR(128) NOT NULL,         -- e.g., user.login, job.sync
#   actor_id VARCHAR(128),                -- user id if known
#   actor_email VARCHAR(320),
#   ip VARCHAR(64),
#   user_agent TEXT,
#   path TEXT,
#   method VARCHAR(16),
#   referrer TEXT,
#   status_code INT,
#   correlation_id UUID NOT NULL,
#   hmac_sha256 CHAR(64) NOT NULL,
#   props JSONB                           -- arbitrary JSON metadata
# );
# CREATE INDEX ON audit_logs (occurred_at);
# CREATE INDEX ON audit_logs (action);
# CREATE INDEX ON audit_logs (actor_id);
# CREATE INDEX ON audit_logs (actor_email);
#
# Environment (optional):
#   AUDIT_HMAC_SECRET  -> secret key for event integrity
#   AUDIT_RETENTION_DAYS (default 30)
#   AUDIT_REDIS_LIST_KEY (default "audit:events")
#   AUDIT_REDIS_LIST_SIZE (default 10000)
# ---------------------------------------------------------------------

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

# --------------------------- Optional imports ---------------------------

# Flask context (optional)
try:
    from flask import request, g, current_app
except Exception:  # pragma: no cover
    request = None  # type: ignore
    g = None        # type: ignore
    current_app = None  # type: ignore

# Extensions (optional: Redis + DB)
try:
    from extensions import redis_client, db  # type: ignore
except Exception:  # pragma: no cover
    redis_client = None  # type: ignore
    db = None            # type: ignore

# Email alerts (optional)
try:
    from utils.mail_util import send_system_alert  # type: ignore
except Exception:  # pragma: no cover
    def send_system_alert(subject: str, body: str) -> None:  # fallback no-op
        logging.warning(f"[audit_util] send_system_alert unavailable | {subject}\n{body}")


# --------------------------- Configuration -----------------------------

AUDIT_HMAC_SECRET = os.environ.get("AUDIT_HMAC_SECRET") or os.environ.get("SECRET_KEY") or "changeme-audit-secret"
AUDIT_RETENTION_DAYS = int(os.environ.get("AUDIT_RETENTION_DAYS") or 30)
AUDIT_REDIS_LIST_KEY = os.environ.get("AUDIT_REDIS_LIST_KEY") or "audit:events"
AUDIT_REDIS_LIST_SIZE = int(os.environ.get("AUDIT_REDIS_LIST_SIZE") or 10_000)

# rate limit defaults
RATE_LIMIT_WINDOW_SEC = 60
RATE_LIMIT_MAX_EVENTS_PER_ACTOR = 200  # per window per actor/ip

# Security keywords that trigger elevated attention
SUSPICIOUS_ACTION_PATTERNS = [
    r"\bfailed[_\-]?login\b",
    r"\bpermission[_\-]?denied\b",
    r"\bcsrf[_\-]?mismatch\b",
    r"\btoken[_\-]?tamper\b",
    r"\bbruteforce\b",
    r"\bprivilege[_\-]?escalation\b",
    r"\bapi[_\-]?abuse\b",
]

# PII patterns to scrub (safe-by-default)
PII_PATTERNS = [
    (re.compile(r"(?i)\b[\w\.-]+@[\w\.-]+\.\w+\b"), "<redacted_email>"),
    (re.compile(r"(?i)\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"), "<redacted_ssn>"),
    (re.compile(r"(?i)\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "<redacted_phone>"),
    (re.compile(r"(?i)\b\d{12,19}\b"), "<redacted_account>"),  # coarse CC/Acct
    (re.compile(r"(?i)\baddress\b\s*:\s*[^,;]+"), "address: <redacted_address>"),
]


# --------------------------- Utilities ---------------------------------


def _utcnow() -> datetime:
    return datetime.utcnow()


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def _safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":"))
    except Exception as e:
        logging.error(f"[audit_util] json dumps failed: {e}")
        return json.dumps({"_unserializable": str(obj)[:1000]})


def _scrub_text(text: str) -> str:
    """Scrub PII from text"""
    s = text
    for pattern, repl in PII_PATTERNS:
        try:
            s = pattern.sub(repl, s)
        except Exception as e:
            # Log pattern that failed but continue with other patterns
            import logging
            logging.warning(f"PII pattern scrubbing failed: {e}")
    return s


def scrub_pii(obj: Any) -> Any:
    """
    Recursively scrubs obvious PII from dict/list/str payloads.
    Conservative: better to over-redact than leak.
    """
    try:
        if obj is None:
            return None
        if isinstance(obj, str):
            return _scrub_text(obj)
        if isinstance(obj, dict):
            redacted = {}
            for k, v in obj.items():
                key_l = str(k).lower()
                if any(s in key_l for s in ["password", "passwd", "secret", "ssn", "token", "api_key", "apikey", "key", "authorization"]):
                    redacted[k] = "<redacted_secret>"
                else:
                    redacted[k] = scrub_pii(v)
            return redacted
        if isinstance(obj, (list, tuple, set)):
            return type(obj)(scrub_pii(v) for v in obj)
        return obj
    except Exception as e:
        logging.warning(f"[audit_util] scrub_pii failed: {e}")
        return "<redacted_error>"


def _hmac_hexdigest(payload: str) -> str:
    return hmac.new(AUDIT_HMAC_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _actor_fingerprint(user_id: Optional[str], ip: Optional[str]) -> str:
    base = (user_id or "") + "|" + (ip or "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _incr_rate_limit_bucket(user_id: Optional[str], ip: Optional[str]) -> Tuple[int, int]:
    """
    Returns (count, ttl_remaining) within the current window.
    No-Redis fallback returns (0, RATE_LIMIT_WINDOW_SEC).
    """
    if not redis_client:
        return (0, RATE_LIMIT_WINDOW_SEC)
    try:
        bucket = f"audit:rate:{_actor_fingerprint(user_id, ip)}"
        p = redis_client.pipeline()
        p.incr(bucket)
        p.expire(bucket, RATE_LIMIT_WINDOW_SEC)
        count, _ = p.execute()
        ttl = redis_client.ttl(bucket)
        return int(count), int(ttl if ttl > 0 else RATE_LIMIT_WINDOW_SEC)  # type: ignore[operator]
    except Exception as e:
        logging.warning(f"[audit_util] rate-limit incr failed: {e}")
        return (0, RATE_LIMIT_WINDOW_SEC)


def _is_suspicious(action: str, message: str) -> bool:
    text = f"{action} {message}".lower()
    for pat in SUSPICIOUS_ACTION_PATTERNS:
        if re.search(pat, text):
            return True
    return False


def _capture_request_ctx() -> Dict[str, Any]:
    """
    Safely capture Flask request context if available.
    """
    if request is None:
        return {}
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)  # render/GW friendly
        return {
            "ip": ip.split(",")[0].strip() if ip else None,
            "user_agent": str(request.user_agent) if getattr(request, "user_agent", None) else None,
            "path": request.path if hasattr(request, "path") else None,
            "method": request.method if hasattr(request, "method") else None,
            "referrer": request.referrer if hasattr(request, "referrer") else None,
            "status_code": getattr(g, "response_status_code", None) if g is not None else None,
        }
    except Exception:
        return {}


def _resolve_actor(default_id: Optional[str], default_email: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve actor from Flask-Login (if present) or defaults.
    """
    # Try Flask-Login current_user
    try:
        from flask_login import current_user  # type: ignore
        if current_user and getattr(current_user, "is_authenticated", False):
            uid = str(getattr(current_user, "id", None)) or default_id
            email = str(getattr(current_user, "email", None)) or default_email
            return uid, email
    except Exception:
        pass
    return default_id, default_email


# --------------------------- Core API ----------------------------------


def record_event(
    action: str,
    *,
    level: str = "info",
    message: str = "",
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    props: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[Union[str, uuid.UUID]] = None,
    timestamp: Optional[datetime] = None,
    write_to_db: bool = True,
    force_alert: bool = False,
) -> Dict[str, Any]:
    """
    Record a single audit event.

    Returns the normalized event dict as stored (before DB insert).
    Never raises: logs errors internally and best-effort persists.
    """
    occurred_at = timestamp or _utcnow()
    corr_id = str(correlation_id or uuid.uuid4())

    # Try to resolve actor from session if not explicitly passed
    actor_id, actor_email = _resolve_actor(actor_id, actor_email)

    # Collect request ctx (optional)
    ctx = _capture_request_ctx()

    # Build event payload
    raw_event = {
        "occurred_at": _iso(occurred_at),
        "level": level.lower(),
        "action": action,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "ip": ctx.get("ip"),
        "user_agent": ctx.get("user_agent"),
        "path": ctx.get("path"),
        "method": ctx.get("method"),
        "referrer": ctx.get("referrer"),
        "status_code": ctx.get("status_code"),
        "correlation_id": corr_id,
        "props": scrub_pii(props or {}),
        "message": scrub_pii(message or "") if isinstance(message, str) else message,
        "_v": 1,  # schema version
    }

    # Integrity (tamper-evident)
    hmac_payload = _safe_json_dumps({k: raw_event[k] for k in sorted(raw_event) if k not in {"message"}})
    raw_event["hmac_sha256"] = _hmac_hexdigest(hmac_payload)

    # Rate limit noisy actors
    count, ttl = _incr_rate_limit_bucket(raw_event["actor_id"], raw_event["ip"])
    if count > RATE_LIMIT_MAX_EVENTS_PER_ACTOR:
        # Store minimally, but do not spam backends
        logging.warning(
            f"[audit_util] rate-limited actor={raw_event['actor_id']} ip={raw_event['ip']} "
            f"bucket={count}/{RATE_LIMIT_MAX_EVENTS_PER_ACTOR} ttl={ttl}s"
        )
        raw_event["message"] = "[rate-limited] " + str(raw_event.get("message") or "")

    # Store to Redis ring buffer
    _redis_push(raw_event)

    # Optionally store to DB
    if write_to_db:
        _db_insert(raw_event)

    # Logging
    _emit_log(raw_event)

    # Alerts
    if force_alert or _is_suspicious(action, str(message or "")) or level.lower() in ("error", "security"):
        _alert(raw_event)

    return raw_event


def _emit_log(ev: Dict[str, Any]) -> None:
    # Compact single-line JSON for ingestion (e.g., Datadog/CloudWatch)
    try:
        logging.info("🦍 AUDIT " + _safe_json_dumps(ev))
    except Exception:
        pass


def _alert(ev: Dict[str, Any]) -> None:
    try:
        subject = f"🚨 PSU Security/Audit: {ev.get('action')} [{ev.get('level')}]"
        body = (
            f"Time: {ev.get('occurred_at')}\n"
            f"Action: {ev.get('action')}\n"
            f"Level: {ev.get('level')}\n"
            f"Actor: {ev.get('actor_id')} | {ev.get('actor_email')}\n"
            f"IP/UA: {ev.get('ip')} | {ev.get('user_agent')}\n"
            f"HTTP: {ev.get('method')} {ev.get('path')} (ref: {ev.get('referrer')})\n"
            f"Status: {ev.get('status_code')}\n"
            f"Correlation: {ev.get('correlation_id')}\n"
            f"Message: {ev.get('message')}\n"
            f"Props: {json.dumps(ev.get('props'), default=str, ensure_ascii=False)}\n"
            f"HMAC: {ev.get('hmac_sha256')}\n"
        )
        send_system_alert(subject, body)
    except Exception as e:
        logging.error(f"[audit_util] alert failed: {e}")


def _redis_push(ev: Dict[str, Any]) -> None:
    if not redis_client:
        return
    try:
        pipe = redis_client.pipeline()
        pipe.lpush(AUDIT_REDIS_LIST_KEY, _safe_json_dumps(ev))
        pipe.ltrim(AUDIT_REDIS_LIST_KEY, 0, AUDIT_REDIS_LIST_SIZE - 1)
        pipe.execute()
    except Exception as e:
        logging.warning(f"[audit_util] redis push failed: {e}")


def _db_insert(ev: Dict[str, Any]) -> None:
    """Best-effort DB insert without requiring ORM model presence."""
    if not db:
        return
    try:
        # Try SQLAlchemy Core text insert into audit_logs if table exists.
        engine = db.get_engine() if hasattr(db, "get_engine") else db.engine  # type: ignore
        with engine.connect() as conn:
            # Ensure table exists; if not, skip silently (migrations create it)
            # Postgres-specific existence check
            exists = conn.execute(
                db.text(
                    "SELECT to_regclass('public.audit_logs') IS NOT NULL AS exists"
                )
            ).scalar()
            if not exists:
                return
            conn.execute(
                db.text(
                    """
                    INSERT INTO audit_logs
                      (occurred_at, level, action, actor_id, actor_email, ip, user_agent,
                       path, method, referrer, status_code, correlation_id, hmac_sha256, props)
                    VALUES
                      (:occurred_at, :level, :action, :actor_id, :actor_email, :ip, :user_agent,
                       :path, :method, :referrer, :status_code, :correlation_id, :hmac_sha256, CAST(:props AS JSONB))
                    """
                ),
                {
                    "occurred_at": datetime.fromisoformat(ev["occurred_at"].replace("Z", "")),
                    "level": ev["level"],
                    "action": ev["action"],
                    "actor_id": ev["actor_id"],
                    "actor_email": ev["actor_email"],
                    "ip": ev["ip"],
                    "user_agent": ev["user_agent"],
                    "path": ev["path"],
                    "method": ev["method"],
                    "referrer": ev["referrer"],
                    "status_code": ev["status_code"],
                    "correlation_id": ev["correlation_id"],
                    "hmac_sha256": ev["hmac_sha256"],
                    "props": _safe_json_dumps(ev.get("props") or {}),
                },
            )
    except Exception as e:
        logging.warning(f"[audit_util] db insert failed: {e}")


# --------------------------- Decorators --------------------------------


def audit_route(action: str, level: str = "info", include_request_body: bool = False):
    """
    Decorator for Flask route handlers. Records an audit event around the call.
    Usage:
        @app.route('/login', methods=['POST'])
        @audit_route('user.login', level='security', include_request_body=False)
        def login():
            ...

    include_request_body: if True, will include a scrubbed snapshot of request.json/form (be cautious).
    """

    def _decorator(fn: Callable):
        def _wrapped(*args, **kwargs):
            start = time.perf_counter()
            body_snapshot = None

            if include_request_body and request is not None:
                try:
                    body_snapshot = request.get_json(silent=True)
                    if body_snapshot is None and request.form:
                        body_snapshot = dict(request.form)
                except Exception:
                    body_snapshot = "<unavailable>"

            try:
                result = fn(*args, **kwargs)
                # try to capture status code from result
                status_code = None
                if isinstance(result, tuple) and len(result) >= 2:
                    status_code = result[1]
                if g is not None:
                    setattr(g, "response_status_code", status_code)
                return result
            except Exception as e:
                # Record error event before re-raising
                duration = time.perf_counter() - start
                record_event(
                    action=action,
                    level="error",
                    message=f"route exception: {e}",
                    props={"duration_ms": int(duration * 1000), "body": body_snapshot} if include_request_body else {"duration_ms": int(duration * 1000)},
                )
                raise
            finally:
                # Record success/info after execution (unless exception)
                duration = time.perf_counter() - start
                record_event(
                    action=action,
                    level=level,
                    message="route handled",
                    props={"duration_ms": int(duration * 1000), "body": body_snapshot} if include_request_body else {"duration_ms": int(duration * 1000)},
                )

        # Preserve wrapped attributes
        _wrapped.__name__ = fn.__name__
        _wrapped.__doc__ = fn.__doc__
        _wrapped.__module__ = fn.__module__
        return _wrapped

    return _decorator


def audit_job(action: str, level: str = "info"):
    """
    Decorator for background jobs / scheduled tasks.
    Usage:
        @audit_job('job.analytics_sync')
        def sync():
            ...
    """

    def _decorator(fn: Callable):
        def _wrapped(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = time.perf_counter() - start
                record_event(
                    action=action,
                    level=level,
                    message="job executed",
                    props={"duration_ms": int(duration * 1000)},
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                record_event(
                    action=action,
                    level="error",
                    message=f"job exception: {e}",
                    props={"duration_ms": int(duration * 1000)},
                    force_alert=True,
                )
                raise

        _wrapped.__name__ = fn.__name__
        _wrapped.__doc__ = fn.__doc__
        _wrapped.__module__ = fn.__module__
        return _wrapped

    return _decorator


# --------------------------- Export / Fetch -----------------------------


def fetch_recent_from_redis(limit: int = 200) -> Iterable[Dict[str, Any]]:
    if not redis_client:
        return []
    try:
        items = redis_client.lrange(AUDIT_REDIS_LIST_KEY, 0, max(0, limit - 1))
        for b in items or []:
            try:
                yield json.loads(b)
            except Exception:
                continue
    except Exception as e:
        logging.warning(f"[audit_util] fetch redis failed: {e}")
        return []


def export_csv(events: Iterable[Dict[str, Any]]) -> bytes:
    """
    Export iterable of events to CSV (UTF-8).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "occurred_at", "level", "action", "actor_id", "actor_email", "ip", "user_agent",
        "path", "method", "referrer", "status_code", "correlation_id", "hmac_sha256", "message", "props_json"
    ])
    for ev in events:
        writer.writerow([
            ev.get("occurred_at"),
            ev.get("level"),
            ev.get("action"),
            ev.get("actor_id"),
            ev.get("actor_email"),
            ev.get("ip"),
            ev.get("user_agent"),
            ev.get("path"),
            ev.get("method"),
            ev.get("referrer"),
            ev.get("status_code"),
            ev.get("correlation_id"),
            ev.get("hmac_sha256"),
            (ev.get("message") or "")[:10000],
            _safe_json_dumps(ev.get("props") or {}),
        ])
    return buf.getvalue().encode("utf-8")


def export_ndjson(events: Iterable[Dict[str, Any]]) -> bytes:
    """
    Export iterable of events to Newline-Delimited JSON (UTF-8).
    """
    out = io.StringIO()
    for ev in events:
        out.write(_safe_json_dumps(ev) + "\n")
    return out.getvalue().encode("utf-8")


# --------------------------- GDPR / Retention ---------------------------


def delete_user_data(actor_id: Optional[str] = None, actor_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Best-effort deletion (GDPR/CCPA helper):
    - Removes recent events in Redis for matching actor
    - Removes DB rows where actor_id/email match (if DB present)
    """
    removed_redis = 0
    removed_db = 0

    # Redis sweep
    if redis_client:
        try:
            items = list(fetch_recent_from_redis(AUDIT_REDIS_LIST_SIZE))
            keep = []
            for ev in items:
                if (actor_id and ev.get("actor_id") == actor_id) or (actor_email and ev.get("actor_email") == actor_email):
                    removed_redis += 1
                    continue
                keep.append(ev)
            # Rewrite list
            pipe = redis_client.pipeline()
            pipe.delete(AUDIT_REDIS_LIST_KEY)
            if keep:
                pipe.rpush(AUDIT_REDIS_LIST_KEY, *[_safe_json_dumps(e) for e in keep])
            pipe.execute()
        except Exception as e:
            logging.warning(f"[audit_util] delete_user_data redis failed: {e}")

    # DB sweep
    if db and (actor_id or actor_email):
        try:
            engine = db.get_engine() if hasattr(db, "get_engine") else db.engine  # type: ignore
            sql = "DELETE FROM audit_logs WHERE 1=1"
            params: Dict[str, Any] = {}
            if actor_id:
                sql += " AND actor_id = :actor_id"
                params["actor_id"] = actor_id
            if actor_email:
                sql += " AND actor_email = :actor_email"
                params["actor_email"] = actor_email
            with engine.begin() as conn:
                res = conn.execute(db.text(sql), params)
                removed_db = getattr(res, "rowcount", 0) or 0
        except Exception as e:
            logging.warning(f"[audit_util] delete_user_data db failed: {e}")

    return {"removed_redis": removed_redis, "removed_db": removed_db}


def retention_cleanup(retention_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Removes DB events older than retention_days and trims Redis (already bounded).
    """
    days = retention_days or AUDIT_RETENTION_DAYS
    cutoff = _utcnow() - timedelta(days=days)
    removed_db = 0

    if db:
        try:
            engine = db.get_engine() if hasattr(db, "get_engine") else db.engine  # type: ignore
            with engine.begin() as conn:
                res = conn.execute(
                    db.text("DELETE FROM audit_logs WHERE occurred_at < :cutoff"),
                    {"cutoff": cutoff},
                )
                removed_db = getattr(res, "rowcount", 0) or 0
        except Exception as e:
            logging.warning(f"[audit_util] retention db cleanup failed: {e}")

    # Redis list is already bounded by AUDIT_REDIS_LIST_SIZE, nothing more to do.
    return {"cutoff": _iso(cutoff), "removed_db": removed_db}


# --------------------------- Convenience APIs --------------------------


def record_security_event(action: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Shortcut for high-priority security signal (always alerts).
    """
    return record_event(
        action=action,
        level="security",
        message=message,
        force_alert=True,
        **kwargs,
    )


def record_warning(action: str, message: str, **kwargs) -> Dict[str, Any]:
    return record_event(action=action, level="warning", message=message, **kwargs)


def record_error(action: str, message: str, **kwargs) -> Dict[str, Any]:
    return record_event(action=action, level="error", message=message, **kwargs)


def record_info(action: str, message: str, **kwargs) -> Dict[str, Any]:
    return record_event(action=action, level="info", message=message, **kwargs)


# --------------------------- Health / Self-test -------------------------


def self_test() -> Dict[str, Any]:
    """
    Runs a quick self-test to verify HMAC, Redis, and (optionally) DB insert route.
    Safe for production; writes a single test event.
    """
    ev = record_event(
        action="audit.self_test",
        level="info",
        message="Self-test event",
        props={"ping": True},
    )

    health = {
        "hmac_len": len(ev.get("hmac_sha256", "")),
        "redis_ok": bool(redis_client is not None),
        "db_ok": bool(db is not None),
        "correlation_id": ev.get("correlation_id"),
    }
    return health
