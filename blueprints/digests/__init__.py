# ==============================================================
# Gorilla-Link / PSU Connect
# blueprints/digests/__init__.py
# ==============================================================

from flask import Blueprint

digests_bp = Blueprint("digests_bp", __name__, url_prefix="/digests")

from . import routes
