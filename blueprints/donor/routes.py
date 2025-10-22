# ============================================================
# FILE: blueprints/donor/routes.py
# ============================================================
from flask import render_template, current_app
from . import donor_bp

@donor_bp.route("/portal", methods=["GET"])
def portal():
    if not current_app.config.get("DONOR_PORTAL_ENABLED", True):
        return render_template("errors/disabled.html", feature="Donor Portal"), 200
    tiers = [
        {"name": "Bronze", "amount": "$1k+", "perks": ["Logo on site & digest"]},
        {"name": "Silver", "amount": "$5k+", "perks": ["Bronze + spotlight feature"]},
        {"name": "Gold", "amount": "$10k+", "perks": ["Silver + event signage"]},
        {"name": "Platinum", "amount": "$25k+", "perks": ["Gold + program naming"]},
    ]
    recent_awards = [
        {"name": "Engineering Leaders Award", "amount": "$2,000", "student": "Maria L."},
        {"name": "First-Gen Scholars Fund", "amount": "$1,500", "student": "James T."},
    ]
    return render_template("donor/portal.html", tiers=tiers, recent_awards=recent_awards)
