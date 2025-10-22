# ============================================================
# FILE: blueprints/scholarships/__init__.py
# ============================================================
from flask import Blueprint

scholarships_bp = Blueprint("scholarships_bp", __name__, url_prefix="/scholarships", template_folder="../../templates/scholarships")

from . import routes  # noqa: E402,F401
