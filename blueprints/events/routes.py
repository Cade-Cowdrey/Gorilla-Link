from flask import Blueprint, render_template
from utils.analytics_util import record_page_view
from flask_login import current_user
from models import Event
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("events", __name__, url_prefix="/events")

@bp.route("/")
def events_home():
    record_page_view("events_home", current_user.id if current_user.is_authenticated else None)
    
    try:
        # Get upcoming events
        upcoming = Event.query.filter(Event.event_date >= datetime.utcnow()).order_by(Event.event_date).limit(20).all()
    except Exception as e:
        logger.error(f"Error loading events: {e}")
        upcoming = []
    
    return render_template("events/index.html", title="Events | PittState-Connect", upcoming=upcoming)
