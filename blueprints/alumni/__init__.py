# ============================================================
# FILE: blueprints/alumni/__init__.py
# ============================================================
from flask import Blueprint

alumni_bp = Blueprint("alumni", __name__, url_prefix="/alumni", template_folder="../../templates/alumni")
bp = alumni_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
