# ============================================================
# FILE: blueprints/careers/__init__.py
# ============================================================
from flask import Blueprint

careers_bp = Blueprint("careers", __name__, url_prefix="/careers", template_folder="../../templates/careers")
bp = careers_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
