# ============================================================
# FILE: blueprints/emails/__init__.py
# ============================================================
from flask import Blueprint

emails_bp = Blueprint("emails_bp", __name__, url_prefix="/emails", template_folder="../../templates/emails")

from . import routes  # noqa: E402,F401
