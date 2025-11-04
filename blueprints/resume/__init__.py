"""
Resume Builder Blueprint - AI-Powered Resume Creation and Optimization
Provides students and alumni with intelligent resume building tools
"""

from flask import Blueprint

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')

from . import routes
