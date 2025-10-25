# blueprints/careers/routes.py
# ---------------------------------------------------------------------
# Careers Blueprint for PittState-Connect
# Provides career dashboards, job listings, employer highlights,
# analytics tracking, and PSU-branded visualizations.
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# ---------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------
from extensions import db, redis_client
from utils.analytics_util import record_page_visit, get_page_stats
from utils.mail_util import send_system_alert

# ---------------------------------------------------------------------
# Blueprint configuration
# ---------------------------------------------------------------------
careers_bp = Blueprint(
    "careers_bp",
    __name__,
    template_folder="templates",
    static_folder="static"
)

# ---------------------------------------------------------------------
# Index (main careers dashboard)
# ---------------------------------------------------------------------
@careers_bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Main PSU Career Hub landing page.
    Displays personalized insights, job listings, analytics metrics,
    and employer recommendations.
    """
    try:
        # Log page visit (async-safe Redis or fallback DB)
        record_page_visit("careers_dashboard", user_id=current_user.id if current_user.is_authenticated else None)

        # Example stats aggregation (from Redis cache or DB fallback)
        stats = get_page_stats("careers_dashboard") or {
            "total_jobs": 128,
            "active_internships": 47,
            "featured_employers": 12,
            "recent_applies": 34,
        }

        # PSU Career Panels
        panels = [
            {"title": "Featured Jobs", "desc": "Top openings curated for PSU students.", "icon": "bi-briefcase"},
            {"title": "Internships", "desc": "Hands-on experience with top employers.", "icon": "bi-mortarboard"},
            {"title": "Employer Partners", "desc": "Connect with PSU’s corporate allies.", "icon": "bi-building"},
            {"title": "Career Resources", "desc": "Guides, templates, and mentoring help.", "icon": "bi-lightbulb"},
        ]

        # Example employer spotlight
        employer_spotlight = {
            "name": "Koch Industries",
            "sector": "Engineering & Business",
            "desc": "Offering graduate internships and leadership programs for PSU Gorillas.",
            "logo": "/static/img/employers/koch.png"
        }

        return render_template(
            "careers/index.html",
            stats=stats,
            panels=panels,
            employer=employer_spotlight,
            now=datetime.utcnow(),
        )

    except SQLAlchemyError as e:
        current_app.logger.error(f"[Careers] DB error: {e}")
        send_system_alert("Careers DB Error", str(e))
        return render_template("errors/500.html"), 500

    except Exception as e:
        current_app.logger.error(f"[Careers] Unhandled exception: {e}")
        send_system_alert("Careers Route Error", str(e))
        return render_template("errors/500.html"), 500


# ---------------------------------------------------------------------
# Jobs API (JSON endpoint)
# ---------------------------------------------------------------------
@careers_bp.route("/api/jobs", methods=["GET"])
@login_required
def api_jobs():
    """
    Returns job listings in JSON (for dynamic UI rendering or analytics tracking).
    """
    try:
        jobs = [
            {"title": "Software Engineer Intern", "company": "Garmin", "location": "Olathe, KS"},
            {"title": "Marketing Assistant", "company": "Freeman Health System", "location": "Joplin, MO"},
            {"title": "Data Analyst", "company": "Kansas City Chiefs", "location": "Kansas City, MO"},
        ]
        return jsonify({"success": True, "jobs": jobs})
    except Exception as e:
        current_app.logger.error(f"[Careers API] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------
# Employer analytics route (for PSU dashboard cards)
# ---------------------------------------------------------------------
@careers_bp.route("/analytics/overview", methods=["GET"])
@login_required
def careers_analytics_overview():
    """
    Returns key analytics metrics for the Careers section dashboard card.
    """
    try:
        metrics = get_page_stats("careers_dashboard") or {}
        return jsonify({
            "page": "careers_dashboard",
            "visits": metrics.get("visits", 0),
            "unique_users": metrics.get("unique_users", 0),
            "avg_time_spent": metrics.get("avg_time_spent", 0),
        })
    except Exception as e:
        current_app.logger.warning(f"[Careers Analytics] Fallback triggered: {e}")
        return jsonify({"page": "careers_dashboard", "visits": 0, "unique_users": 0, "avg_time_spent": 0})
