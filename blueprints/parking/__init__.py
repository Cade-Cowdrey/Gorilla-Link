from flask import Blueprint

parking_bp = Blueprint('parking', __name__, url_prefix='/parking')
bp = parking_bp  # Export as bp for auto-registration

from . import routes
