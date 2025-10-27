"""
PittState-Connect | Analytics Utility
Tracks API usage, page views, and aggregates stats for dashboards.
Includes Redis caching for fast PSU analytics.
"""

from datetime import datetime, timedelta
from loguru import logger
from extensions import db, redis_client
from models import PageView, ApiUsage


# ======================================================
# 📈 RECORD PAGE VIEWS
# ======================================================
def record_page_view(page, user_id=None):
    try:
        view = PageView(page=page, user_id=user_id)
        db.session.add(view)
        db.session.commit()
        logger.info(f"📊 Logged page view: {page} (user={user_id})")
    except Exception as e:
        logger.error(f"❌ Failed to log page view: {e}")


# ======================================================
# 🔍 RECORD API USAGE
# ======================================================
def record_api_usage(endpoint, method, user_id=None):
    try:
        log = ApiUsage(endpoint=endpoint, method=method, user_id=user_id)
        db.session.add(log)
        db.session.commit()
        logger.info(f"🛰️ API hit logged: {endpoint} [{method}] (user={user_id})")
    except Exception as e:
        logger.error(f"❌ Failed to log API usage: {e}")


# ======================================================
# 🧠 PAGE STATS
# ======================================================
def get_page_stats(days=7):
    """Returns cached analytics summary for last N days."""
    cache_key = f"page_stats:{days}"
    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                import json
                logger.info("📊 Returning cached page stats.")
                return json.loads(cached)

        cutoff = datetime.utcnow() - timedelta(days=days)
        results = (
            db.session.query(PageView.page, db.func.count(PageView.id))
            .filter(PageView.timestamp >= cutoff)
            .group_by(PageView.page)
            .all()
        )

        stats = {page: count for page, count in results}
        if redis_client:
            redis_client.setex(cache_key, 3600, str(stats))
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to retrieve page stats: {e}")
        return {}
