from flask import Blueprint

sublease_bp = Blueprint('sublease', __name__, url_prefix='/sublease')

from . import routes
