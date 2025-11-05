"""
Free Certifications Blueprint
Browse free certifications from top providers like Google, Microsoft, AWS, HubSpot
"""
from flask import Blueprint

bp = Blueprint('certifications', __name__, url_prefix='/certifications')

from . import routes
