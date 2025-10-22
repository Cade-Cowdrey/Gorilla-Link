# ============================================================
# FILE: blueprints/notifications/__init__.py
# ============================================================
from flask import Blueprint

notifications_bp = Blueprint("notifications_bp", __name__, url_prefix="/notifications", template_folder="../../templates/notifications")

from . import routes  # noqa: E402,F401
