from flask import Blueprint, render_template, request, session
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
    PSU-branded landing page – PittState-Connect core homepage.
    Displays hero message and quick access to app features.
    """
    hero = {
        "title": "Welcome to PittState-Connect",
        "subtitle": "Your digital bridge between students, alumni, employers, and opportunity.",
        "cta": "Start exploring scholarships, mentors, and careers today.",
        "image": "/static/images/psu-campus-hero.jpg"
    }

    logger.info("🦍 Rendering home page.")
    return render_template(
        "core/home.html",
        title="Home | PittState-Connect",
        hero=hero
    )


# ==========================================================
# 📖 ABOUT
# ==========================================================

@core_bp.route("/about")
@track_page_view
def about():
    info = {
        "mission": "Connecting the Gorilla community — empowering PSU students, alumni, and employers.",
        "vision": "To make PittState the #1 connected university in the Midwest.",
        "values": ["Innovation", "Integrity", "Community", "Growth"]
    }
    return render_template(
        "core/about.html",
        title="About | PittState-Connect",
        info=info
    )


# ==========================================================
# 🧠 HEALTH CHECK & ANALYTICS TEST
# ==========================================================

@core_bp.route("/ping")
def ping():
    """
    Basic health check endpoint for Render and monitoring.
    """
    logger.info("✅ Health check ping successful.")
    record_page_view("ping")
    return {"status": "ok", "service": "PittState-Connect"}


# ==========================================================
# ⚙️ MAINTENANCE / COMING SOON
# ==========================================================

@core_bp.route("/coming-soon")
def coming_soon():
    return render_template("errors/coming_soon.html", title="Coming Soon | PittState-Connect")


@core_bp.route("/maintenance")
def maintenance():
    return render_template("errors/maintenance.html", title="Maintenance Mode | PittState-Connect")
