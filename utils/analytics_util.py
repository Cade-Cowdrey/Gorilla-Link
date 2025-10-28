from extensions import db
from models import PageView, ApiUsage
from loguru import logger
from datetime import datetime

# ----------------------------
# PAGE VIEWS
# ----------------------------

def record_page_view(page_name, user_id=None, ip_address=None, user_agent=None):
    """Record a page view safely."""
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


def track_page_view(endpoint_func):
    """Decorator to automatically log page views for routes."""
    from functools import wraps
    from flask import request, g

    @wraps(endpoint_func)
    def wrapper(*args, **kwargs):
        try:
            user_id = getattr(g, "user_id", None)
            record_page_view(
                page_name=request.path,
                user_id=user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent")
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-track page view: {e}")
        return endpoint_func(*args, **kwargs)
    return wrapper


def get_page_stats(limit=20):
    """Return most-viewed pages."""
    try:
        results = (
            db.session.query(PageView.page_name, db.func.count(PageView.id).label("views"))
            .group_by(PageView.page_name)
            .order_by(db.desc("views"))
            .limit(limit)
            .all()
        )
        return [{"page": r.page_name, "views": r.views} for r in results]
    except Exception as e:
        logger.error(f"❌ get_page_stats failed: {e}")
        return []


# ----------------------------
# API USAGE TRACKING
# ----------------------------

def record_api_usage(endpoint, method, status_code, user_id=None):
    """Log API usage metrics."""
    try:
        entry = ApiUsage(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user_id=user_id,
            timestamp=datetime.utcnow(),
        )
        db.session.add(entry)
        db.session.commit()
        logger.info(f"✅ API logged: {method} {endpoint} [{status_code}]")
    except Exception as e:
        logger.error(f"❌ record_api_usage failed: {e}")
        db.session.rollback()
