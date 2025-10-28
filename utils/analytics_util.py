from extensions import db
from models import PageView
from loguru import logger
from datetime import datetime

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
