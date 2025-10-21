import importlib
import pkgutil
from flask import Blueprint


def register_all_blueprints(app):
    """
    Automatically discovers and registers every Blueprint that defines `bp`
    inside each package under /blueprints.
    """

    pkg_name = __name__  # "blueprints"

    for finder, package_name, ispkg in pkgutil.iter_modules(__path__):
        if not ispkg:
            continue

        package = importlib.import_module(f"{pkg_name}.{package_name}")

        # Walk through submodules inside each package
        if hasattr(package, "__path__"):
            for _, modname, ispkg2 in pkgutil.iter_modules(package.__path__):
                if ispkg2:
                    continue
                module = importlib.import_module(f"{package.__name__}.{modname}")
                bp = getattr(module, "bp", None)
                if isinstance(bp, Blueprint):
                    app.register_blueprint(bp)
                    print(f"✅ Registered blueprint: {bp.name} ({package_name})")

    print("✅ All blueprints registered successfully.")
