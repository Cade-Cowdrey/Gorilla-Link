"""
Push Notifications Blueprint Routes
Imports the main push_notifications blueprint from __init__.py
"""

from blueprints.push_notifications import push_notifications_bp

# This file exists to allow the blueprint auto-discovery system
# to find and register the push_notifications blueprint
# The actual routes are defined in blueprints/push_notifications/__init__.py

__all__ = ['push_notifications_bp']

# Export the blueprint with the expected name
bp = push_notifications_bp
