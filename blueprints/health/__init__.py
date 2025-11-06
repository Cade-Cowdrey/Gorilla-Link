# ============================================================
# FILE: blueprints/health/__init__.py
# ============================================================
from flask import Blueprint

health_bp = Blueprint("health", __name__, url_prefix="/health", template_folder="../../templates/health")
bp = health_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
