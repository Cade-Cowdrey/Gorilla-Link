# ============================================================
# FILE: blueprints/departments/__init__.py
# ============================================================
from flask import Blueprint

departments_bp = Blueprint("departments_bp", __name__, url_prefix="/departments", template_folder="../../templates/departments")

from . import routes  # noqa: E402,F401
