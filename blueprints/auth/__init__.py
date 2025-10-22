# ============================================================
# FILE: blueprints/auth/__init__.py
# ============================================================
from flask import Blueprint

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth", template_folder="../../templates/auth")

from . import routes  # noqa: E402,F401
