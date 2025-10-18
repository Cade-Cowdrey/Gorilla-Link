import os, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BP_DIR = ROOT / "blueprints"

def detect_bp_var(text):
    m = re.search(r"(\w+)\s*=\s*Blueprint\(", text)
    return m.group(1) if m else None

def desired_init(folder, var_name, import_from_routes):
    if import_from_routes and var_name:
        return f"from .routes import {var_name} as bp\n"
    # fallback: simple bp for 'from . import bp' pattern
    name = folder.name
    return "from flask import Blueprint\nbp = Blueprint('%s', __name__)\n" % name

def main():
    if not BP_DIR.exists():
        print("❌ No blueprints directory found.")
        sys.exit(1)

    for d in BP_DIR.iterdir():
        if not d.is_dir():
            continue
        routes = d / "routes.py"
        wrong = d / "_init_.py"
        correct = d / "__init__.py"

        if wrong.exists():
            wrong.unlink()

        var_name = None
        if routes.exists():
            text = routes.read_text(encoding="utf-8", errors="ignore")
            var_name = detect_bp_var(text)

        init_text = desired_init(d, var_name, import_from_routes=bool(var_name))
        correct.write_text(init_text, encoding="utf-8")

        print(f"✅ {correct.relative_to(ROOT)} → bp = {var_name or '<default>'}")

if __name__ == "__main__":
    sys.exit(main())
