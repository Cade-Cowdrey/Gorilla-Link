# ============================================================
# FILE: blueprints/scholarships/__init__.py
# ============================================================
from flask import Blueprint

scholarships_bp = Blueprint("scholarships", __name__, url_prefix="/scholarships", template_folder="../../templates/scholarships")
bp = scholarships_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
