from extensions import db
from models import PageView, ApiUsage
from loguru import logger
from datetime import datetime
from functools import wraps
from flask import request, g

# ==========================================================
# 🧠 ANALYTICS & METRICS UTILITIES
# ==========================================================

def record_page_view(page_name, user_id=None, ip_address=None, user_agent=None):
    """
    Record a single page view safely in the database.
    Called manually or by @track_page_view decorator.
    """
    try:
        view = PageView(
            page_name=page_name,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        db.session.add(view)
        db.session.commit()
        logger.info(f"✅ Logged page view: {page_name}")
    except Exception as e:
        logger.error(f"❌ record_page_view failed: {e}")
        db.session.rollback()


def track_page_view(func):
    """
    Decorator to automatically record a page view
    whenever a route is accessed.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            user_id = getattr(g, "user_id", None)
            ip = request.remote_addr
            ua = request.headers.get("User-Agent")
            record_page_view(
                page_name=request.path,
                user_id=user_id,
                ip_address=ip,
                user_agent=ua
            )
        except Exception as e:
            logger.warning(f"⚠️ Auto-track page view failed: {e}")
        return func(*args, **kwargs)
    return wrapper


def get_page_stats(limit=20):
    """
    Return the most viewed pages (for admin dashboards or analytics panels).
    """
    try:
        results = (
            db.session.query(PageView.page_name, db.func.count(PageView.id).label("views"))
            .group_by(PageView.page_name)
            .order_by(db.desc("views"))
            .limit(limit)
            .all()
        )
        stats = [{"page": r.page_name, "views": r.views} for r in results]
        logger.info(f"📊 Retrieved {len(stats)} page view stats")
        return stats
    except Exception as e:
        logger.error(f"❌ get_page_stats failed: {e}")
        return []


def get_top_pages(limit=20):
    """
    Alias for get_page_stats - returns the most viewed pages.
    Used by analytics blueprint.
    """
    return get_page_stats(limit)


def record_api_usage(endpoint, method, status_code, user_id=None):
    """
    Log API usage and performance metrics.
    """
    try:
        entry = ApiUsage(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user_id=user_id,
            timestamp=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()
        logger.info(f"✅ API logged: {method} {endpoint} [{status_code}]")
    except Exception as e:
        logger.error(f"❌ record_api_usage failed: {e}")
        db.session.rollback()


def get_api_stats(limit=25):
    """
    Return the most frequently accessed API endpoints for analytics dashboards.
    """
    try:
        results = (
            db.session.query(ApiUsage.endpoint, db.func.count(ApiUsage.id).label("hits"))
            .group_by(ApiUsage.endpoint)
            .order_by(db.desc("hits"))
            .limit(limit)
            .all()
        )
        return [{"endpoint": r.endpoint, "hits": r.hits} for r in results]
    except Exception as e:
        logger.error(f"❌ get_api_stats failed: {e}")
        return []
