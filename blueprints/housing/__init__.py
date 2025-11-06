# ============================================================
# FILE: blueprints/housing/__init__.py
# ============================================================
from flask import Blueprint

housing_bp = Blueprint("housing", __name__, url_prefix="/housing", template_folder="../../templates/housing")
bp = housing_bp  # Alias for auto-registration

from . import routes  # noqa: E402,F401
