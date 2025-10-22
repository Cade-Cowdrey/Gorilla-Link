# ============================================================
# FILE: blueprints/mentors/__init__.py
# ============================================================
from flask import Blueprint

mentors_bp = Blueprint("mentors_bp", __name__, url_prefix="/mentors", template_folder="../../templates/mentors")

from . import routes  # noqa: E402,F401
