from flask import Blueprint

parking_bp = Blueprint('parking', __name__, url_prefix='/parking')

from . import routes
