from flask import Flask
from .config import Config
from .extensions import db, cache, compress, limiter
from .utils import init_security_headers, init_oauth_if_configured, seed_admin_if_empty
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    db.init_app(app); cache.init_app(app); compress.init_app(app); limiter.init_app(app)
    Talisman(app, content_security_policy=None); init_security_headers(app)
    with app.app_context():
        from .models import User
        db.create_all(); seed_admin_if_empty(app)
    init_oauth_if_configured(app)
    from .blueprints.core.routes import bp as core_bp
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.departments.routes import bp as dept_bp
    from .blueprints.alumni.routes import bp as alumni_bp
    from .blueprints.students.routes import bp as students_bp
    from .blueprints.opportunities.routes import bp as opps_bp
    from .blueprints.admin.routes import bp as admin_bp
    from .blueprints.api.routes import bp as api_bp
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dept_bp, url_prefix="/departments")
    app.register_blueprint(alumni_bp, url_prefix="/alumni")
    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(opps_bp, url_prefix="/opportunities")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
