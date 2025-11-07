from flask import Blueprint

study_groups_bp = Blueprint('study_groups', __name__, url_prefix='/study-groups')
bp = study_groups_bp  # Export as bp for auto-registration

from . import routes
