import importlib, pkgutil
from flask import Blueprint

def register_all_blueprints(app):
    from . import core, careers, analytics, alumni, scholarships, admin, emails, auth, departments, donor
    packages = [core, careers, analytics, alumni, scholarships, admin, emails, auth, departments, donor]
    for pkg in packages:
        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
            if ispkg:
                continue
            module = importlib.import_module(f"{pkg.__name__}.{modname}")
            if hasattr(module, "bp") and isinstance(module.bp, Blueprint):
                app.register_blueprint(module.bp)
