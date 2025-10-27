"""
PittState-Connect | Analytics Utilities
Tracks page views and API usage with Redis caching for PSU dashboards.
"""

from datetime import datetime, timedelta
from loguru import logger
from extensions import db, redis_client
from models import PageView, ApiUsage


# ======================================================
# 📈 PAGE VIEWS
# ======================================================
def record_page_view(page, user_id=None):
    try:
        view = PageView(page=page, user_id=user_id)
        db.session.add(view)
        db.session.commit()
        logger.info(f"📊 Page view recorded: {page} (user={user_id})")
    except Exception as e:
        logger.error(f"❌ record_page_view failed: {e}")


def track_page_view(page_name, user_id=None):
    """Alias for backward compatibility."""
    try:
        record_page_view(page_name, user_id)
    except Exception as e:
        logger.error(f"track_page_view failed: {e}")


# ======================================================
# 🔍 API USAGE
# ======================================================
def record_api_usage(endpoint, method, user_id=None):
    try:
        log = ApiUsage(endpoint=endpoint, method=method, user_id=user_id)
        db.session.add(log)
        db.session.commit()
        logger.info(f"🛰️ API usage recorded: {endpoint} [{method}] (user={user_id})")
    except Exception as e:
        logger.error(f"❌ record_api_usage failed: {e}")


# ======================================================
# 🧠 PAGE STATS
# ======================================================
def get_page_stats(days=7):
    """Fetch aggregated page stats for the past N days (cached)."""
    cache_key = f"page_stats:{days}"
    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                import json
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
            import json
            redis_client.setex(cache_key, 3600, json.dumps(stats))

        return stats
    except Exception as e:
        logger.error(f"❌ get_page_stats failed: {e}")
        return {}
