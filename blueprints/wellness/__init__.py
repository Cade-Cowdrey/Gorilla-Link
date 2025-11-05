from flask import Blueprint

wellness_bp = Blueprint('wellness', __name__, url_prefix='/wellness')

from . import routes
