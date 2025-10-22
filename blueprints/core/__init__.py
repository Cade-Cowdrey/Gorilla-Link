# ============================================================
# FILE: blueprints/core/__init__.py
# ============================================================
from flask import Blueprint

core_bp = Blueprint("core_bp", __name__, url_prefix="/", template_folder="../../templates/core")

from . import routes  # noqa: E402,F401
