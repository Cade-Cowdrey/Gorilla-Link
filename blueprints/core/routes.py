from flask import Blueprint, render_template, current_app, request

core_bp = Blueprint("core", __name__, template_folder="templates/core")


@core_bp.route("/")
def home():
    """Landing page — PSU-branded home with safe conditional CTA."""
    current_app.logger.info("🏠 Home route accessed successfully.")
    has_register = "auth.register" in current_app.view_functions
    return render_template(
        "core/home.html",
        title="PittState-Connect | Home",
        has_register=has_register,
    )


@core_bp.route("/team")
def team():
    return render_template("core/team.html", title="Our Team | PittState-Connect")


@core_bp.route("/careers")
def careers():
    return render_template("core/careers.html", title="Careers | PittState-Connect")


@core_bp.route("/events")
def events():
    return render_template("core/events.html", title="Events | PittState-Connect")


@core_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Simple contact page (fallback when register isn’t available)."""
    if request.method == "POST":
        # You can wire this to email/log later; for now we just thank the user.
        current_app.logger.info("📨 Contact form submitted.")
        return render_template(
            "core/contact.html",
            title="Contact | PittState-Connect",
            submitted=True,
        )
    return render_template("core/contact.html", title="Contact | PittState-Connect")


@core_bp.route("/status")
def status():
    return (
        "✅ PittState-Connect is running — all blueprints loaded successfully.",
        200,
        {"Content-Type": "text/plain"},
    )
