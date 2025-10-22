# ============================================================
# FILE: blueprints/__init__.py
# Central blueprint exports + feature-flag toggles + safe stubs
# PittState-Connect
# ============================================================

from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional
from flask import Blueprint

log = logging.getLogger(__name__)

# ------------------------------------------------------------
# Helper: Create a harmless stub blueprint if import fails
# ------------------------------------------------------------
def _stub_bp(name: str, url_prefix: str, reason: str) -> Blueprint:
    """
    Returns a tiny blueprint that won't break the app if a real blueprint
    can't be imported. Renders a minimal HTML message at its root.
    """
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    @bp.route("/", strict_slashes=False)
    def _stub_index():
        return (
            f"<h1>{name} (stub)</h1>"
            f"<p>This feature is currently disabled or not installed.</p>"
            f"<small>Reason: {reason}</small>",
            200,
        )

    log.warning("Using STUB blueprint for %s (%s). Reason: %s", name, url_prefix, reason)
    return bp


# ------------------------------------------------------------
# Helper: Read feature flags (env → bool)
# ------------------------------------------------------------
def _flag(key: str, default: bool = True) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return str(v).lower() in {"1", "true", "yes", "on"}


FEATURE_FLAGS = {
    # Community & content
    "ALUMNI_PORTAL_ENABLED": _flag("ALUMNI_PORTAL_ENABLED", True),
    "DEPARTMENT_PAGES_ENABLED": _flag("DEPARTMENT_PAGES_ENABLED", True),
    "MENTORSHIP_PROGRAM_ENABLED": _flag("MENTORSHIP_PROGRAM_ENABLED", True),
    "MESSAGING_ENABLED": _flag("MESSAGING_ENABLED", True),
    "EVENTS_ENABLED": _flag("EVENTS_ENABLED", True),

    # Careers / Scholarships / Donors
    "CAREERS_BOARD_ENABLED": _flag("CAREERS_BOARD_ENABLED", True),
    "SCHOLARSHIP_HUB_ENABLED": _flag("SCHOLARSHIP_HUB_ENABLED", True),
    "DONOR_PORTAL_ENABLED": _flag("DONOR_PORTAL_ENABLED", True),

    # Notifications & Emails
    "NOTIFICATIONS_ENABLED": _flag("NOTIFICATIONS_ENABLED", True),

    # Analytics / Gamification (doesn't gate blueprint import, only pages)
    "ANALYTICS_DASHBOARD": _flag("ANALYTICS_DASHBOARD", True),
}


# ------------------------------------------------------------
# Try to import each real blueprint package; if it fails, stub it.
# Each subpackage should expose a <name>_bp object.
# ------------------------------------------------------------
def _try_import(module_path: str, attr: str, fallback_name: str, prefix: str) -> Blueprint:
    try:
        mod = __import__(module_path, fromlist=[attr])
        bp: Blueprint = getattr(mod, attr)  # type: ignore
        if not isinstance(bp, Blueprint):
            raise TypeError(f"{module_path}.{attr} did not provide a Blueprint")
        log.info("Loaded blueprint: %s (%s)", fallback_name, prefix)
        return bp
    except Exception as e:
        return _stub_bp(fallback_name, prefix, reason=str(e))


# Core (always on)
core_bp         = _try_import("blueprints.core",         "core_bp",         "core_bp",         "/")
auth_bp         = _try_import("blueprints.auth",         "auth_bp",         "auth_bp",         "/auth")

# Careers (gated)
if FEATURE_FLAGS["CAREERS_BOARD_ENABLED"]:
    careers_bp  = _try_import("blueprints.careers",      "careers_bp",      "careers_bp",      "/careers")
else:
    careers_bp  = _stub_bp("careers_bp", "/careers", "Feature flag CAREERS_BOARD_ENABLED=False")

# Departments (gated)
if FEATURE_FLAGS["DEPARTMENT_PAGES_ENABLED"]:
    departments_bp = _try_import("blueprints.departments","departments_bp", "departments_bp",  "/departments")
else:
    departments_bp = _stub_bp("departments_bp", "/departments", "Feature flag DEPARTMENT_PAGES_ENABLED=False")

# Scholarships (gated)
if FEATURE_FLAGS["SCHOLARSHIP_HUB_ENABLED"]:
    scholarships_bp = _try_import("blueprints.scholarships","scholarships_bp","scholarships_bp","/scholarships")
else:
    scholarships_bp = _stub_bp("scholarships_bp", "/scholarships", "Feature flag SCHOLARSHIP_HUB_ENABLED=False")

# Mentors (gated)
if FEATURE_FLAGS["MENTORSHIP_PROGRAM_ENABLED"]:
    mentors_bp   = _try_import("blueprints.mentors",     "mentors_bp",      "mentors_bp",      "/mentors")
else:
    mentors_bp   = _stub_bp("mentors_bp", "/mentors", "Feature flag MENTORSHIP_PROGRAM_ENABLED=False")

# Alumni (gated)
if FEATURE_FLAGS["ALUMNI_PORTAL_ENABLED"]:
    alumni_bp    = _try_import("blueprints.alumni",      "alumni_bp",       "alumni_bp",       "/alumni")
else:
    alumni_bp    = _stub_bp("alumni_bp", "/alumni", "Feature flag ALUMNI_PORTAL_ENABLED=False")

# Analytics (usually on, but dynamic pages inside may check flags)
analytics_bp    = _try_import("blueprints.analytics",    "analytics_bp",    "analytics_bp",    "/analytics")

# Donor (gated)
if FEATURE_FLAGS["DONOR_PORTAL_ENABLED"]:
    donor_bp     = _try_import("blueprints.donor",       "donor_bp",        "donor_bp",        "/donor")
else:
    donor_bp     = _stub_bp("donor_bp", "/donor", "Feature flag DONOR_PORTAL_ENABLED=False")

# Emails (system email previews, usually always on)
emails_bp       = _try_import("blueprints.emails",       "emails_bp",       "emails_bp",       "/emails")

# Notifications (gated)
if FEATURE_FLAGS["NOTIFICATIONS_ENABLED"]:
    notifications_bp = _try_import("blueprints.notifications","notifications_bp","notifications_bp","/notifications")
else:
    notifications_bp = _stub_bp("notifications_bp", "/notifications", "Feature flag NOTIFICATIONS_ENABLED=False")


# ------------------------------------------------------------
# Optional one-liner registrar (if you want to use it in app_pro)
# Example usage:
#   from blueprints import register_all
#   register_all(app)
# ------------------------------------------------------------
def register_all(app) -> List[str]:
    """
    Registers every exported blueprint on the provided Flask app.
    Returns a list of registered names for logging/diagnostics.
    """
    to_register: List[Blueprint] = [
        core_bp,
        auth_bp,
        careers_bp,
        departments_bp,
        scholarships_bp,
        mentors_bp,
        alumni_bp,
        analytics_bp,
        donor_bp,
        emails_bp,
        notifications_bp,
    ]
    registered: List[str] = []
    for bp in to_register:
        # Avoid double-registration during tests
        if bp.name in app.blueprints:
            continue
        app.register_blueprint(bp)
        log.info("✅ Registered blueprint: %s (%s)", bp.name, bp.url_prefix or "root")
        registered.append(bp.name)
    if registered:
        log.info("✅ All blueprints registered successfully.")
    return registered


# ------------------------------------------------------------
# Public exports (so `from blueprints import X_bp` works)
# ------------------------------------------------------------
__all__ = [
    "core_bp",
    "auth_bp",
    "careers_bp",
    "departments_bp",
    "scholarships_bp",
    "mentors_bp",
    "alumni_bp",
    "analytics_bp",
    "donor_bp",
    "emails_bp",
    "notifications_bp",
    "FEATURE_FLAGS",
    "register_all",
]
