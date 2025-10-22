# ============================================================
# FILE: blueprints/careers/__init__.py
# ============================================================
from flask import Blueprint

careers_bp = Blueprint("careers_bp", __name__, url_prefix="/careers", template_folder="../../templates/careers")

from . import routes  # noqa: E402,F401
