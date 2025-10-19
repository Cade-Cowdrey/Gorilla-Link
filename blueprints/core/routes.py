from flask import Blueprint, render_template, current_app

core_bp = Blueprint("core", __name__, template_folder="templates/core")

@core_bp.route("/")
def home():
    """Landing page — PSU-branded home."""
    current_app.logger.info("🏠 Home route accessed successfully.")
    return render_template("core/home.html", title="PittState-Connect | Home")


@core_bp.route("/about")
def about():
    """About page — explains the platform’s mission."""
    current_app.logger.info("📘 About page accessed.")
    return render_template("core/about.html", title="About | PittState-Connect")


@core_bp.route("/team")
def team():
    """Meet the Team page."""
    current_app.logger.info("👥 Team page accessed.")
    return render_template("core/team.html", title="Our Team | PittState-Connect")


@core_bp.route("/careers")
def careers():
    """Careers info page (static overview, separate from /careers dashboard)."""
    current_app.logger.info("💼 Careers overview accessed.")
    return render_template("core/careers.html", title="Careers | PittState-Connect")


@core_bp.route("/events")
def events():
    """Events overview page."""
    current_app.logger.info("📅 Events overview accessed.")
    return render_template("core/events.html", title="Events | PittState-Connect")


@core_bp.route("/status")
def status():
    """Debug/health route to verify blueprints are active."""
    return (
        "✅ PittState-Connect is running — all blueprints loaded successfully.",
        200,
        {"Content-Type": "text/plain"},
    )
