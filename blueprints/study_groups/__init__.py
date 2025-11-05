from flask import Blueprint

study_groups_bp = Blueprint('study_groups', __name__, url_prefix='/study-groups')

from . import routes
