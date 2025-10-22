# ============================================================
# FILE: blueprints/donor/__init__.py
# ============================================================
from flask import Blueprint

donor_bp = Blueprint("donor_bp", __name__, url_prefix="/donor", template_folder="../../templates/donor")

from . import routes  # noqa: E402,F401
