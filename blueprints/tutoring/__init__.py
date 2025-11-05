from flask import Blueprint

tutoring_bp = Blueprint('tutoring', __name__, url_prefix='/tutoring')

from . import routes
