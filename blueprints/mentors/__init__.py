# ============================================================
# FILE: blueprints/mentors/__init__.py
# ============================================================
from flask import Blueprint

mentors_bp = Blueprint("mentors", __name__, url_prefix="/mentors", template_folder="../../templates/mentors")
bp = mentors_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
