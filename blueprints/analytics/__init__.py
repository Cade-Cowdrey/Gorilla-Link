# ============================================================
# FILE: blueprints/analytics/__init__.py
# ============================================================
from flask import Blueprint

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics", template_folder="../../templates/analytics")

from . import routes  # noqa: E402,F401
