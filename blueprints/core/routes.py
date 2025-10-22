from flask import Blueprint, render_template

# Create the core blueprint
core_bp = Blueprint("core_bp", __name__, template_folder="templates", url_prefix="/")

# -------------------------------
#  PSU CORE ROUTES
# -------------------------------

@core_bp.route("/")
def home():
    return render_template("core/home.html")

@core_bp.route("/about")
def about():
    return render_template("core/about.html")

@core_bp.route("/team")
def team():
    return render_template("core/team.html")

@core_bp.route("/careers")
def careers():
    return render_template("core/careers.html")

@core_bp.route("/events")
def events():
    return render_template("core/events.html")

# Optional public landing route (for SEO or marketing)
@core_bp.route("/welcome")
def welcome():
    return render_template("core/welcome.html")
