from flask import Blueprint

sublease_bp = Blueprint('sublease', __name__, url_prefix='/sublease')
bp = sublease_bp  # Export as bp for auto-registration

from . import routes
