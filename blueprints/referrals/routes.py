"""
Referrals Blueprint Routes
Imports the main referral blueprint from parent directory
"""

from blueprints.referrals import referral_bp

# This file exists to allow the blueprint auto-discovery system
# to find and register the referrals blueprint
# The actual routes are defined in blueprints/referrals.py

__all__ = ['referral_bp']

# Export the blueprint with the expected name
bp = referral_bp
