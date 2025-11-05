from flask import Blueprint

free_stuff_bp = Blueprint('free_stuff', __name__, url_prefix='/free-stuff')

from . import routes
