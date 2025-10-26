from flask import current_app

def init_faculty_blueprint(app):
    """
    Initialize the Faculty blueprint with safety, caching, and PSU-brand logging.
    """
    from .routes import faculty_bp

    try:
        app.register_blueprint(faculty_bp)
        current_app.logger.info("✅ Registered faculty_bp at /faculty")
    except Exception as e:
        current_app.logger.error(f"⚠️ Faculty blueprint registration failed: {e}")
