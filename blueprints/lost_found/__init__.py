from flask import Blueprint

lost_found_bp = Blueprint('lost_found', __name__, url_prefix='/lost-found')
bp = lost_found_bp  # Export as bp for auto-registration

from . import routes
