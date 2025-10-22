import os
from flask import Flask
from datetime import datetime

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Config
    app.config.from_object("config.Config")

    # Jinja globals
    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year}

    # ---- BLUEPRINTS ----
    # Core (home/about/team/etc.)
    from blueprints.core.routes import core_bp
    app.register_blueprint(core_bp)
    print("✅ Registered blueprint: core_bp (core)")

    # Auth
    from blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    print("✅ Registered blueprint: auth_bp (auth)")

    # Careers
    from blueprints.careers.routes import careers_bp
    app.register_blueprint(careers_bp, url_prefix="/careers")
    print("✅ Registered blueprint: careers_bp (careers)")

    # Departments
    from blueprints.departments.routes import departments_bp
    app.register_blueprint(departments_bp, url_prefix="/departments")
    print("✅ Registered blueprint: departments_bp (departments)")

    # Scholarships (Phase 2)
    from blueprints.scholarships.routes import scholarships_bp
    app.register_blueprint(scholarships_bp, url_prefix="/scholarships")
    print("✅ Registered blueprint: scholarships_bp (scholarships)")

    # Mentorship (Phase 3)
    from blueprints.mentors.routes import mentors_bp
    app.register_blueprint(mentors_bp, url_prefix="/mentors")
    print("✅ Registered blueprint: mentors_bp (mentors)")

    # Alumni directory / engagement
    from blueprints.alumni.routes import alumni_bp
    app.register_blueprint(alumni_bp, url_prefix="/alumni")
    print("✅ Registered blueprint: alumni_bp (alumni)")

    # Analytics (Phase 4)
    from blueprints.analytics.routes import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    print("✅ Registered blueprint: analytics_bp (analytics)")

    # Donor / Sponsorship (Phase 5)
    from blueprints.donor.routes import donor_bp
    app.register_blueprint(donor_bp, url_prefix="/donor")
    print("✅ Registered blueprint: donor_bp (donor)")

    # Emails (newsletter, digests)
    from blueprints.emails.routes import emails_bp
    app.register_blueprint(emails_bp, url_prefix="/emails")
    print("✅ Registered blueprint: emails_bp (emails)")

    # Notifications (reminders, deadline pings)
    from blueprints.notifications.routes import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    print("✅ Registered blueprint: notifications_bp (notifications)")

    print("✅ All blueprints registered successfully.")
    return app

# Gunicorn entrypoint
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
