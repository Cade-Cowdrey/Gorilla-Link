# ==============================================================
# Gorilla-Link / Pitt State Connect
# blueprints/__init__.py — Blueprint Package Initializer
# ==============================================================
# Features:
# ✅ Ensures all submodules (blueprints) are valid packages
# ✅ Enables dynamic registration in app_pro.py
# ✅ Safe to run even if some blueprints are missing
# ==============================================================

import os
import importlib

# Dynamically discover and import all blueprints in this package
__all__ = []

base_dir = os.path.dirname(__file__)

for name in os.listdir(base_dir):
    subdir = os.path.join(base_dir, name)
    if os.path.isdir(subdir) and os.path.exists(os.path.join(subdir, "__init__.py")):
        try:
            importlib.import_module(f"blueprints.{name}")
            __all__.append(name)
            print(f"✅ Loaded blueprint package: {name}")
        except Exception as e:
            print(f"⚠️  Skipped blueprint {name}: {e}")
