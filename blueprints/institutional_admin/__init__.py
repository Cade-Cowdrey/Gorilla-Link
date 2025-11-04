"""
Institutional Admin Dashboard Blueprint
University-level administrative controls and reporting
"""

from flask import Blueprint

bp = Blueprint('institutional_admin', __name__, url_prefix='/institutional-admin')

from . import routes
