import importlib
import pkgutil
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from config import load_config, validate_config
from extensions import db, migrate, login_manager, cache, csrf, limiter
from app_extensions import init_all as init_app_extras


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_relative_config=False,
    )

    # -------------------------
    # Config
    # -------------------------
    cfg = load_config()
    app.config.from_object(cfg)
    validate_config(cfg)

    # -------------------------
    # Core extensions
    # -------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # CORS (if you have external clients/mobile app); adjust origins in prod
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # App-wide extras: filters, errors, security headers, logging, request IDs
    init_app_extras(app)

    # -------------------------
    # Blueprints
    # -------------------------
    register_core_blueprints(app)

    # -------------------------
    # Health & diagnostics
    # -------------------------
    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.get("/readyz")
    def readyz():
        # simple DB ping
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "ready"})
        except Exception as e:
            app.logger.exception("readiness probe failed")
            return jsonify({"status": "error", "detail": str(e)}), 500

    return app


def register_core_blueprints(app: Flask):
    """
    Auto-discovers blueprints in ./blueprints/*/__init__.py that expose a `bp` object,
    e.g. blueprints/admin/__init__.py -> bp = Blueprint('admin', __name__, url_prefix='/admin')
    """
    if not app.config.get("ENABLE_BLUEPRINT_AUTODISCOVERY", True):
        return

    root = Path(__file__).parent / "blueprints"
    if not root.exists():
        app.logger.info("No blueprints/ directory found; skipping autodiscovery.")
        return

    for finder, name, ispkg in pkgutil.iter_modules([str(root)]):
        pkg_name = f"blueprints.{name}"
        try:
            mod = importlib.import_module(pkg_name)
        except Exception as e:
            app.logger.exception(f"Failed importing {pkg_name}: {e}")
            continue

        # If package: load its __init__.py expecting a 'bp' attribute
        bp = getattr(mod, "bp", None)
        if bp is not None:
            app.register_blueprint(bp)
            app.logger.info(f"Registered blueprint: {bp.name} (/{bp.url_prefix or ''})")
        else:
            # If module didn't expose bp at package level, try routes submodule
            try:
                routes = importlib.import_module(f"{pkg_name}.routes")
                bp = getattr(routes, "bp", None)
                if bp is not None:
                    app.register_blueprint(bp)
                    app.logger.info(f"Registered blueprint: {bp.name} (/{bp.url_prefix or ''})")
            except Exception as e:
                app.logger.debug(f"No routes module for {pkg_name} or no bp found: {e}")
