from flask import Blueprint

lost_found_bp = Blueprint('lost_found', __name__, url_prefix='/lost-found')

from . import routes
