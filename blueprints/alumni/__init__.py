# ============================================================
# FILE: blueprints/alumni/__init__.py
# ============================================================
from flask import Blueprint

alumni_bp = Blueprint("alumni_bp", __name__, url_prefix="/alumni", template_folder="../../templates/alumni")

from . import routes  # noqa: E402,F401
