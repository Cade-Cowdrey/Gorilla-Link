from flask import Blueprint

tutoring_bp = Blueprint('tutoring', __name__, url_prefix='/tutoring')
bp = tutoring_bp  # Export as bp for auto-registration

from . import routes
