"""
PittState-Connect | Security Utilities
Includes login safety wrapper and role-based protections.
"""

from flask_login import login_required
from functools import wraps
from flask import redirect, url_for, flash


def login_required_safe(f):
    """Safely apply login_required without crashing if user isn't logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return login_required(f)(*args, **kwargs)
        except Exception:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
    return decorated_function
