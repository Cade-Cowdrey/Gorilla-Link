from flask import Blueprint

free_stuff_bp = Blueprint('free_stuff', __name__, url_prefix='/free-stuff')
bp = free_stuff_bp  # Export as bp for auto-registration

from . import routes
