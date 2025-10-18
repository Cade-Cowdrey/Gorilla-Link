"""
🧩 check_blueprints.py
Verifies that all blueprints load correctly and expose a Blueprint named `bp`.

Usage:
    python tools/check_blueprints.py
"""

import importlib
import inspect
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BP_DIR = ROOT / "blueprints"

sys.path.insert(0, str(ROOT))  # allow "import blueprints.xyz"


def is_blueprint(obj):
    """Return True if object is a Flask Blueprint."""
    try:
        from flask import Blueprint
        return isinstance(obj, Blueprint)
    except Exception:
        return False


def check_blueprint(bp_name):
    """Try importing the blueprint and verify its structure."""
    try:
        module = importlib.import_module(f"blueprints.{bp_name}")
    except Exception as e:
        print(f"❌ Failed to import {bp_name}: {e}")
        return False

    # Look for bp variable
    if hasattr(module, "bp") and is_blueprint(module.bp):
        print(f"✅ {bp_name}: valid Blueprint object found")
        return True
    else:
        found = [n for n, v in vars(module).items() if is_blueprint(v)]
        if found:
            print(f"⚠️  {bp_name}: found Blueprint(s) {found}, but no variable named `bp`")
        else:
            print(f"❌ {bp_name}: no Blueprint instance found at all")
        return False


def main():
    if not BP_DIR.exists():
        print("❌ No blueprints/ directory found.")
        sys.exit(1)

    all_dirs = [d.name for d in BP_DIR.iterdir() if d.is_dir()]
    print(f"\n🔍 Checking {len(all_dirs)} blueprints...\n")

    passed, failed = 0, 0
    for bp_name in all_dirs:
        if check_blueprint(bp_name):
            passed += 1
        else:
            failed += 1

    print("\n------------------------------------")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("------------------------------------\n")

    if failed:
        sys.exit(1)
    else:
        print("🎉 All blueprints verified successfully!")


if __name__ == "__main__":
    main()
