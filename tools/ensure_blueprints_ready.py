"""
tools/ensure_blueprints_ready.py
--------------------------------
Creates all required blueprint folders, route files, and PSU-branded
index.html templates if any are missing. Safe to re-run anytime.
"""

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BP_PATH = os.path.join(ROOT, "blueprints")
TPL_PATH = os.path.join(ROOT, "templates")

BLUEPRINTS = {
    "careers": "Career Center",
    "departments": "Departments Hub",
    "scholarships": "Scholarship Hub",
    "mentors": "Mentorship Hub",
    "alumni": "Alumni Network",
    "analytics": "Analytics Dashboard",
    "donor": "Donor Portal",
    "emails": "Email Suite",
    "notifications": "Notifications Center",
}

ROUTE_TEMPLATE = """from flask import Blueprint, render_template
from extensions import limiter

{bp}_bp = Blueprint("{bp}_bp", __name__, url_prefix="/{bp}")

@{bp}_bp.route("/", methods=["GET"])
@limiter.limit("60/minute")
def index():
    return render_template("{bp}/index.html")
"""

HTML_TEMPLATE = """{% extends "base.html" %}
{% block title %}{{ title }} · PittState-Connect{% endblock %}
{% block content %}
<div class="p-5 mb-4 bg-white rounded-3 shadow-sm">
  <div class="container-fluid py-5 text-center">
    <h1 class="display-6 fw-bold">{{ title }}</h1>
    <p class="fs-5 text-muted">Welcome to the {{ title }} — part of the PittState-Connect ecosystem.</p>
    <a class="btn btn-warning mt-3" href="{{ url_for('core_bp.home') }}">Back to Home</a>
  </div>
</div>
{% endblock %}
"""

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Created {path}")

def create_blueprint(bp, title):
    bp_dir = os.path.join(BP_PATH, bp)
    tpl_dir = os.path.join(TPL_PATH, bp)
    ensure_dir(bp_dir)
    ensure_dir(tpl_dir)

    # routes.py
    route_file = os.path.join(bp_dir, "routes.py")
    if not os.path.exists(route_file):
        with open(route_file, "w", encoding="utf-8") as f:
            f.write(ROUTE_TEMPLATE.format(bp=bp))
        print(f"✅ Created {route_file}")

    # template
    tpl_file = os.path.join(tpl_dir, "index.html")
    if not os.path.exists(tpl_file):
        with open(tpl_file, "w", encoding="utf-8") as f:
            f.write(HTML_TEMPLATE.replace("{{ title }}", title))
        print(f"✅ Created {tpl_file}")

if __name__ == "__main__":
    print("🚀 Ensuring all PittState-Connect blueprints exist...")
    for bp, title in BLUEPRINTS.items():
        create_blueprint(bp, title)
    print("🎯 All blueprints verified or created successfully!")
