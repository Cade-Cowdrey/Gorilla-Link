# ==============================================================
# Gorilla-Link / Pitt State Connect
# generate_blueprints.py — Auto-create + Validate + Sync Blueprints
# ==============================================================
# Features:
# ✅ Auto-creates missing blueprint folders (admin, analytics, etc.)
# ✅ Validates structure (__init__.py, routes.py, templates/)
# ✅ Updates app_pro.py to auto-register all valid blueprints
# ✅ Adds a global /healthz route (for Render health checks)
# ==============================================================

import os
import re
from textwrap import dedent

# --------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(__file__)
BLUEPRINTS_DIR = os.path.join(PROJECT_ROOT, "blueprints")
APP_PRO_PATH = os.path.join(PROJECT_ROOT, "app_pro.py")

EXPECTED_BLUEPRINTS = [
    "admin",
    "analytics",
    "auth",
    "badges",
    "careers",
    "campus",
    "core",
    "departments",
    "emails",
    "alumni",
]

# --------------------------------------------------------------
# FILE TEMPLATES
# --------------------------------------------------------------
INIT_TEMPLATE = dedent('''\
    # ==============================================================
    # Gorilla-Link / Pitt State Connect
    # Blueprint Package Initializer
    # ==============================================================
    from flask import Blueprint

    blueprint_name = __name__.split(".")[-1]
    globals()[f"{blueprint_name}_bp"] = Blueprint(
        blueprint_name,
        __name__,
        url_prefix=f"/{blueprint_name}",
        template_folder="templates",
        static_folder="static",
    )

    from . import routes  # noqa: E402, F401
''')

ROUTES_TEMPLATE = dedent('''\
    # ==============================================================
    # Gorilla-Link / Pitt State Connect
    # Example routes for blueprint
    # ==============================================================
    from flask import render_template
    from . import {name}_bp

    @{name}_bp.route("/")
    def index():
        return render_template("{name}/index.html", title="{title}")
''')

HTML_TEMPLATE = dedent('''\
    <!-- ===========================================================
         Gorilla-Link / Pitt State Connect
         {title} Blueprint Default Template
         =========================================================== -->
    {% extends "base.html" %}
    {% block content %}
    <div class="container text-center mt-5">
        <h1 class="text-3xl font-bold text-gorilla-dark mb-4">{title}</h1>
        <p class="text-gray-600">This is the default page for the {title} blueprint.</p>
    </div>
    {% endblock %}
''')

# --------------------------------------------------------------
# BLUEPRINT CREATION
# --------------------------------------------------------------
def create_blueprint(name):
    bp_dir = os.path.join(BLUEPRINTS_DIR, name)
    os.makedirs(os.path.join(bp_dir, "templates", name), exist_ok=True)

    init_path = os.path.join(bp_dir, "__init__.py")
    routes_path = os.path.join(bp_dir, "routes.py")
    html_path = os.path.join(bp_dir, "templates", name, "index.html")

    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(INIT_TEMPLATE)
        print(f"🧩 Created: {init_path}")

    if not os.path.exists(routes_path):
        with open(routes_path, "w", encoding="utf-8") as f:
            f.write(ROUTES_TEMPLATE.format(name=name, title=name.capitalize()))
        print(f"🛠️  Created: {routes_path}")

    if not os.path.exists(html_path):
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(HTML_TEMPLATE.format(title=name.capitalize()))
        print(f"🖼️  Created: {html_path}")

# --------------------------------------------------------------
# VALIDATION LOGIC
# --------------------------------------------------------------
def validate_blueprints():
    print("\n🔍 Validating blueprints for structure and registration...\n")
    issues_found = False
    valid_blueprints = []

    for folder in os.listdir(BLUEPRINTS_DIR):
        bp_path = os.path.join(BLUEPRINTS_DIR, folder)
        if not os.path.isdir(bp_path):
            continue

        init_file = os.path.join(bp_path, "__init__.py")
        routes_file = os.path.join(bp_path, "routes.py")

        if not os.path.exists(init_file) or not os.path.exists(routes_file):
            print(f"⚠️  {folder}/ missing __init__.py or routes.py")
            issues_found = True
            continue

        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()
            if f"{folder}_bp" in content:
                valid_blueprints.append(folder)
            else:
                print(f"⚠️  {folder}/__init__.py missing `{folder}_bp` variable.")
                issues_found = True

    if not issues_found:
        print("✅ All blueprints are valid and properly structured!\n")
    else:
        print("\n🚨 Validation complete — some blueprints may need fixes.\n")

    return valid_blueprints

# --------------------------------------------------------------
# UPDATE app_pro.py TO REGISTER BLUEPRINTS + HEALTH CHECK
# --------------------------------------------------------------
def update_app_pro(valid_blueprints):
    if not os.path.exists(APP_PRO_PATH):
        print("❌ app_pro.py not found in project root!")
        return

    with open(APP_PRO_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Add register_blueprints() or replace it
    pattern = r"def register_blueprints\(app\):[\s\S]+?^\s*return"
    new_function = dedent('''\
        def register_blueprints(app):
            """Auto-register all Flask blueprints."""
            from importlib import import_module
            print("\\n🚀 Registering Flask Blueprints...\\n")

            blueprints = {bplist}

            for name in blueprints:
                try:
                    module = import_module(f"blueprints.{name}")
                    bp = getattr(module, f"{name}_bp", None)
                    if bp:
                        app.register_blueprint(bp)
                        print(f"✅ Registered: {name}")
                    else:
                        print(f"⚠️  Skipped: {name} (no blueprint found)")
                except Exception as e:
                    print(f"❌ Error registering {name}: {{e}}")

            # Health Check Route (used by Render)
            @app.route("/healthz")
            def health_check():
                return {"status": "ok", "message": "Gorilla-Link running"}, 200

            return
    ''').format(bplist=valid_blueprints)

    if re.search(pattern, content, flags=re.MULTILINE):
        new_content = re.sub(pattern, new_function, content, flags=re.MULTILINE)
        print("🔄 Updated existing register_blueprints() in app_pro.py.")
    else:
        new_content = content.strip() + "\n\n" + new_function
        print("➕ Added new register_blueprints() to app_pro.py.")

    with open(APP_PRO_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("💾 app_pro.py successfully updated with blueprints + health check!\n")

# --------------------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------------------
def main():
    print("\n🚧 Running Gorilla-Link Blueprint Generator + Sync Tool...\n")

    if not os.path.exists(BLUEPRINTS_DIR):
        os.makedirs(BLUEPRINTS_DIR)
        print(f"📁 Created blueprints directory: {BLUEPRINTS_DIR}")

    for bp in EXPECTED_BLUEPRINTS:
        create_blueprint(bp)

    valid_blueprints = validate_blueprints()
    update_app_pro(valid_blueprints)

    print("🎉 Blueprint generation, validation, and sync complete!\n")

if __name__ == "__main__":
    main()
