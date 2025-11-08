"""
Gamification Blueprint Routes
Imports the main gamification blueprint from __init__.py
"""

from blueprints.gamification import gamification_bp

# This file exists to allow the blueprint auto-discovery system
# to find and register the gamification blueprint
# The actual routes are defined in blueprints/gamification/__init__.py

__all__ = ['gamification_bp']

# Export the blueprint with the expected name
bp = gamification_bp
