from flask import Blueprint

rideshare_bp = Blueprint('rideshare', __name__, url_prefix='/rideshare')

from . import routes
