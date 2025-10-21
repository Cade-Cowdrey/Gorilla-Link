import importlib, pkgutil
from flask import Blueprint

def register_all_blueprints(app):
    # Discover top-level packages inside blueprints/
    pkg_name = __name__  # "blueprints"
    for finder, package_name, ispkg in pkgutil.iter_modules(__path__):
        if not ispkg:
            # skip plain modules here; we only want packages
            continue
        package = importlib.import_module(f"{pkg_name}.{package_name}")

        # Walk modules inside each package and register any with a Blueprint named "bp"
        if hasattr(package, "__path__"):
            for _, modname, ispkg2 in pkgutil.iter_modules(package.__path__):
                if ispkg2:
                    continue
                module = importlib.import_module(f"{package.__name__}.{modname}")
                bp = getattr(module, "bp", None)
                if isinstance(bp, Blueprint):
                    app.register_blueprint(bp)
