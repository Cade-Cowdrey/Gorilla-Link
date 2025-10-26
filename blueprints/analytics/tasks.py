"""
tasks.py — scheduled analytics jobs for PSU Connect
"""

from extensions import cache, db, redis_client
from loguru import logger
from datetime import datetime

def refresh_insight_cache():
    """Refresh cached analytics data nightly."""
    try:
        logger.info(f"♻️ Refreshing analytics cache at {datetime.utcnow()}")
        metrics = {
            "users_active": db.session.execute("SELECT COUNT(*) FROM user").scalar(),
            "scholarships": db.session.execute("SELECT COUNT(*) FROM scholarship").scalar(),
        }
        cache.set("analytics:summary", metrics, timeout=86400)
        if redis_client:
            redis_client.set("last_analytics_refresh", datetime.utcnow().isoformat())
        logger.success("✅ Analytics cache refreshed successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to refresh analytics cache: {e}")
