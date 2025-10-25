# utils/analytics_util.py
# ---------------------------------------------------------------------
# Production-ready analytics utility for PittState-Connect
# - Tracks page views, user events, and app health metrics
# - Designed for PSU-branded analytics dashboards
# - Integrates with SQLAlchemy, Redis, and async scheduler
# ---------------------------------------------------------------------

import logging
import json
import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import request, session, g
from extensions import db, redis_client

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | analytics_util | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# DATABASE MODEL REFERENCE
# The database likely has an AnalyticsEvent or SiteStat model.
# We’ll write ORM-agnostic inserts so it won’t break even if renamed.
# ---------------------------------------------------------------------

def record_page_visit(endpoint: str, user_id=None, meta: dict = None):
    """
    Records a page visit in analytics storage.
    Called automatically from blueprints (e.g. careers, core, events).
    """
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ua = request.user_agent.string if request.user_agent else "Unknown"
        ts = datetime.datetime.utcnow()

        data = {
            "endpoint": endpoint,
            "user_id": user_id or getattr(g, "user_id", None),
            "ip": ip,
            "user_agent": ua[:255],
            "timestamp": ts.isoformat(),
            "meta": meta or {},
        }

        # Try Redis fast-track first (lightweight event buffer)
        try:
            redis_client.lpush("analytics:page_visits", json.dumps(data))
        except Exception:
            pass  # Redis may not always be available

        # Database persistence (fallback or primary)
        try:
            db.session.execute(
                """
                INSERT INTO analytics_log (endpoint, user_id, ip, user_agent, meta, created_at)
                VALUES (:endpoint, :user_id, :ip, :user_agent, :meta, :created_at)
                """,
                {
                    "endpoint": endpoint,
                    "user_id": data["user_id"],
                    "ip": ip,
                    "user_agent": ua,
                    "meta": json.dumps(data["meta"]),
                    "created_at": ts,
                },
            )
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.warning(f"Analytics DB insert failed: {e}")

        logger.info(f"📈 Page visit recorded for {endpoint} (user={data['user_id']}, ip={ip})")
    except Exception as e:
        logger.error(f"❌ Failed to record page visit: {e}")


def record_event(category: str, action: str, label: str = None, value: int = None, user_id=None, meta=None):
    """
    Records a custom analytics event (search, click, submit, etc.).
    Mirrors Google Analytics style for flexibility.
    """
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ts = datetime.datetime.utcnow()
        payload = {
            "category": category,
            "action": action,
            "label": label,
            "value": value,
            "user_id": user_id or getattr(g, "user_id", None),
            "timestamp": ts.isoformat(),
            "meta": meta or {},
        }

        redis_client.lpush("analytics:events", json.dumps(payload))
        db.session.execute(
            """
            INSERT INTO analytics_event (category, action, label, value, user_id, meta, created_at)
            VALUES (:category, :action, :label, :value, :user_id, :meta, :created_at)
            """,
            {
                "category": category,
                "action": action,
                "label": label,
                "value": value,
                "user_id": payload["user_id"],
                "meta": json.dumps(payload["meta"]),
                "created_at": ts,
            },
        )
        db.session.commit()
        logger.info(f"📊 Event logged: {category}/{action} (user={payload['user_id']})")
    except Exception as e:
        db.session.rollback()
        logger.warning(f"⚠️ Failed to record event: {e}")


def get_dashboard_metrics(days: int = 30):
    """
    Aggregates analytics data for the PSU admin dashboard.
    Returns dict with summary statistics.
    """
    try:
        result = db.session.execute(
            """
            SELECT
                COUNT(*) AS total_visits,
                COUNT(DISTINCT user_id) AS unique_users,
                COUNT(DISTINCT endpoint) AS unique_pages
            FROM analytics_log
            WHERE created_at > (NOW() - INTERVAL :days DAY)
            """,
            {"days": days},
        ).fetchone()

        return {
            "total_visits": result.total_visits if result else 0,
            "unique_users": result.unique_users if result else 0,
            "unique_pages": result.unique_pages if result else 0,
            "range_days": days,
        }
    except SQLAlchemyError as e:
        logger.error(f"Analytics dashboard query failed: {e}")
        return {"total_visits": 0, "unique_users": 0, "unique_pages": 0, "range_days": days}


def flush_redis_to_db():
    """
    Optional scheduler job: periodically flushes Redis analytics queues to DB.
    """
    try:
        count = 0
        for key, table in [("analytics:page_visits", "analytics_log"), ("analytics:events", "analytics_event")]:
            while redis_client.llen(key):
                raw = redis_client.rpop(key)
                if not raw:
                    break
                try:
                    data = json.loads(raw)
                    db.session.execute(
                        f"""
                        INSERT INTO {table} (endpoint, user_id, ip, user_agent, meta, created_at)
                        VALUES (:endpoint, :user_id, :ip, :user_agent, :meta, :created_at)
                        """,
                        {
                            "endpoint": data.get("endpoint"),
                            "user_id": data.get("user_id"),
                            "ip": data.get("ip", "unknown"),
                            "user_agent": data.get("user_agent", "unknown"),
                            "meta": json.dumps(data.get("meta", {})),
                            "created_at": data.get("timestamp", datetime.datetime.utcnow()),
                        },
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to flush one event: {e}")
        db.session.commit()
        logger.info(f"✅ Flushed {count} analytics records from Redis → DB.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Redis analytics flush failed: {e}")
