from flask import Blueprint

wellness_bp = Blueprint('wellness', __name__, url_prefix='/wellness')
bp = wellness_bp  # Export as bp for auto-registration

from . import routes
