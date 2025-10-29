from flask import Blueprint, render_template, request
from flask_login import current_user
from utils.analytics_util import track_page_view, record_page_view
from loguru import logger

core_bp = Blueprint("core_bp", __name__)

# ==========================================================
# 🏠 HOME / LANDING
# ==========================================================

@core_bp.route("/")
@track_page_view
def home():
    """
    PSU-branded landing page for PittState-Connect.
    Automatically tracks views and logs user analytics.
    """
    # ✅ Correct function call for analytics logging
    record_page_view(
        page_name="home",
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Your PSU ecosystem for students, alumni, and employers.",
        "cta": "Explore scholarships, connections, and careers today.",
        "image": "/static/images/psu-campus-hero.jpg",
    }

    logger.info("🦍 Rendering Home page")
    return render_template(
        "core/home.html",
        title="Home | PittState-Connect",
        hero=hero,
    )


# ==========================================================
# 📖 ABOUT
# ==========================================================

@core_bp.route("/about")
@track_page_view
def about():
    record_page_view(
        page_name="about",
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    info = {
        "mission": "Connecting the Gorilla community — empowering PSU students, alumni, and employers.",
        "vision": "To make PittState the #1 connected university in the Midwest.",
        "values": ["Innovation", "Integrity", "Community", "Growth"],
    }

    return render_template(
        "core/about.html",
        title="About | PittState-Connect",
        info=info,
    )


# ==========================================================
# 🧠 HEALTH CHECK / STATUS
# ==========================================================

@core_bp.route("/ping")
def ping():
    record_page_view("ping")
    return {"status": "ok", "service": "PittState-Connect"}


# ==========================================================
# ⚙️ MAINTENANCE / COMING SOON
# ==========================================================

@core_bp.route("/coming-soon")
def coming_soon():
    return render_template(
        "errors/coming_soon.html",
        title="Coming Soon | PittState-Connect"
    )


@core_bp.route("/maintenance")
def maintenance():
    return render_template(
        "errors/maintenance.html",
        title="Maintenance Mode | PittState-Connect"
    )
