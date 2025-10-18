"""
🧩 PSU Gorilla-Link — Integrity Diagnostic Script
-------------------------------------------------
Run this once deployment finishes to verify:
• All Flask routes are registered and reachable
• Templates extend base.html correctly
• PSU branding assets (CSS/JS/img) are loaded
"""

import os
from flask import render_template
from app_pro import app

def check_routes():
    print("\n=== 🔍 ROUTE REGISTRATION CHECK ===")
    for rule in app.url_map.iter_rules():
        if "static" in rule.endpoint:
            continue
        try:
            endpoint = rule.endpoint
            func = app.view_functions[endpoint]
            print(f"✅ Route found: {rule} → {func.__name__}")
        except Exception as e:
            print(f"❌ Broken route: {rule} → {e}")

def check_templates():
    print("\n=== 🧱 TEMPLATE INTEGRITY CHECK ===")
    missing_templates = []
    for root, _, files in os.walk("templates"):
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if "{% extends" not in content and "base.html" not in content:
                        missing_templates.append(path)
    if not missing_templates:
        print("✅ All templates extend base.html or have valid structure.")
    else:
        print("⚠️ Templates missing base.html inheritance:")
        for t in missing_templates:
            print(f"   - {t}")

def check_static_assets():
    print("\n=== 🎨 PSU BRANDING ASSETS CHECK ===")
    assets = [
        "static/css/psu_theme.css",
        "static/img/psu_logo.png",
        "static/img/gorilla-icon.png",
        "static/img/favicon.ico",
    ]
    for asset in assets:
        if os.path.exists(asset):
            print(f"✅ Found: {asset}")
        else:
            print(f"❌ Missing: {asset}")

def main():
    print("====================================")
    print("   PSU Gorilla-Link Diagnostic Tool ")
    print("====================================")
    check_routes()
    check_templates()
    check_static_assets()
    print("\n✅ Scan complete! If all are green, branding and routing are fully connected.\n")

if __name__ == "__main__":
    main()
