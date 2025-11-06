# ============================================================
# FILE: blueprints/safety/__init__.py
# ============================================================
from flask import Blueprint

safety_bp = Blueprint("safety", __name__, url_prefix="/safety", template_folder="../../templates/safety")
bp = safety_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
