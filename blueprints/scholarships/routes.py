# blueprints/scholarships/routes.py
from flask import Blueprint, render_template, redirect, url_for
from extensions import limiter

scholarships_bp = Blueprint("scholarships_bp", __name__, url_prefix="/scholarships")

@scholarships_bp.route("/", methods=["GET"])
@limiter.limit("60/minute")
def index():
    # your real logic / data goes here
    return render_template("scholarships/index.html")

# Backward compatibility for templates that still point to .hub
@scholarships_bp.route("/hub", methods=["GET"])
@limiter.limit("60/minute")
def hub():
    return redirect(url_for("scholarships_bp.index"), code=301)
