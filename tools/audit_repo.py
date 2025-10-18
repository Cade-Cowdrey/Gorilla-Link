#!/usr/bin/env python3
"""
Repo Audit for PittState-Connect / Gorilla-Link
Scans blueprints, models, templates, imports, and generates a Markdown report.

USAGE:
  python tools/audit_repo.py

OUTPUT:
  audit_report.md  (human-readable)
  audit_report.json (machine-readable)
"""
import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Set

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINTS_DIR = ROOT / "blueprints"
TEMPLATES_DIR = ROOT / "templates"
UTILS_DIR = ROOT / "utils"
MODELS_PY = ROOT / "models.py"
APP_PRO = ROOT / "app_pro.py"
REQUIREMENTS = ROOT / "requirements.txt"

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def py_imports(source: str) -> Dict[str, List[str]]:
    """Parse python file imports (ast)."""
    out = {"import": [], "from": []}
    try:
        tree = ast.parse(source)
    except Exception:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                out["import"].append(alias.name)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            names = [a.name for a in n.names]
            out["from"].append(f"{mod}: {', '.join(names)}")
    return out

def find_blueprint_bp_names(source: str) -> List[str]:
    """
    Return variables that look like <name>_bp = Blueprint("<name>", ...)
    """
    pat = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*Blueprint\(\s*[\'"]([a-zA-Z0-9_\-]+)[\'"]\s*,', re.M)
    return [m.group(1) for m in pat.finditer(source)]

def find_url_prefix(source: str) -> str:
    m = re.search(r'Blueprint\([^)]*url_prefix\s*=\s*[\'"]([^\'"]+)[\'"]', source)
    return m.group(1) if m else ""

def find_routes(source: str) -> List[str]:
    pat = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*)\.route\(\s*[\'"]([^\'"]+)[\'"]\s*,?\s*methods\s*=\s*\[([^\]]+)\]', re.M)
    out = []
    for m in pat.finditer(source):
        bp_var = m.group(1)
        route = m.group(2)
        methods = re.sub(r"\s", "", m.group(3))
        out.append(f"{bp_var}.route('{route}', methods=[{methods}])")
    return out

def find_render_templates(source: str) -> Set[str]:
    pat = re.compile(r'render_template\(\s*[\'"]([^\'"]+)[\'"]', re.M)
    return set(m.group(1) for m in pat.finditer(source))

def find_model_symbols(source: str) -> Set[str]:
    """
    Capture names imported from 'models'.
    """
    out = set()
    try:
        tree = ast.parse(source)
    except Exception:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "models":
            for a in n.names:
                out.add(a.name)
    return out

def list_templates_used_but_missing(templates: Set[str]) -> List[str]:
    missing = []
    for t in templates:
        if not (TEMPLATES_DIR / t).exists():
            missing.append(t)
    return missing

def models_defined() -> Set[str]:
    source = read_text(MODELS_PY)
    out = set()
    try:
        tree = ast.parse(source)
    except Exception:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            out.add(n.name)
    return out

def mail_exports_defined() -> Set[str]:
    util = read_text(UTILS_DIR / "mail_util.py")
    pat = re.compile(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\(', re.M)
    return set(pat.findall(util))

def grep_mail_uses() -> Set[str]:
    """Find functions imported from utils.mail_util across blueprints."""
    used = set()
    for p in BLUEPRINTS_DIR.rglob("*.py"):
        src = read_text(p)
        try:
            tree = ast.parse(src)
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module == "utils.mail_util":
                for a in n.names:
                    used.add(a.name)
    return used

def detect_relative_import_issues(src: str) -> bool:
    return "from .." in src or "from ..." in src

def audit_blueprint(bp_dir: Path, defined_models: Set[str], mail_defs: Set[str]) -> Dict[str, Any]:
    entry = {"name": bp_dir.name, "routes_files": [], "status": "ok", "problems": []}
    routes_py = bp_dir / "routes.py"
    if not routes_py.exists():
        entry["status"] = "missing"
        entry["problems"].append("routes.py missing")
        return entry

    src = read_text(routes_py)
    imports = py_imports(src)
    bp_vars = find_blueprint_bp_names(src)
    url_prefix = find_url_prefix(src)
    routes = find_routes(src)
    templates = find_render_templates(src)
    models_used = find_model_symbols(src)
    rel_issue = detect_relative_import_issues(src)

    missing_models = sorted([m for m in models_used if m not in defined_models])
    missing_templates = list_templates_used_but_missing(templates)

    entry.update({
        "routes_files": [str(routes_py.relative_to(ROOT))],
        "blueprint_vars": bp_vars,
        "url_prefix": url_prefix,
        "routes": routes,
        "imports": imports,
        "models_used": sorted(list(models_used)),
        "missing_models": missing_models,
        "templates_used": sorted(list(templates)),
        "missing_templates": sorted(missing_templates),
        "relative_import_issue": rel_issue
    })

    if not bp_vars:
        entry["status"] = "problem"
        entry["problems"].append("No <name>_bp = Blueprint(...) variable exported")

    if rel_issue:
        entry["status"] = "problem"
        entry["problems"].append("Relative import detected (use absolute imports e.g., from models import X)")

    if missing_models:
        entry["status"] = "problem"
        entry["problems"].append(f"Missing model classes: {', '.join(missing_models)}")

    if missing_templates:
        entry["status"] = "problem"
        entry["problems"].append(f"Missing templates: {', '.join(missing_templates)}")

    return entry

def main():
    report: Dict[str, Any] = {
        "root": str(ROOT),
        "summary": {},
        "blueprints": [],
        "files": []
    }

    # Collect basic file tree
    for p in sorted(ROOT.rglob("*")):
        if any(seg.startswith(".venv") or seg == "__pycache__" for seg in p.parts):
            continue
        report["files"].append(str(p.relative_to(ROOT)))

    defined_models = models_defined()
    mail_defs = mail_exports_defined()
    mail_used = grep_mail_uses()

    report["summary"]["defined_models"] = sorted(list(defined_models))
    report["summary"]["mail_util_functions"] = sorted(list(mail_defs))
    report["summary"]["mail_util_functions_used"] = sorted(list(mail_used))
    report["summary"]["mail_util_missing_functions"] = sorted(list(mail_used - mail_defs))

    # app_pro blueprint list sanity
    app_pro_txt = read_text(APP_PRO)
    bp_names = re.findall(r'blueprints\s*=\s*\[[^\]]+\]', app_pro_txt, re.S)
    report["summary"]["app_pro_blueprints_list_found"] = bool(bp_names)

    # Audit each blueprint
    if BLUEPRINTS_DIR.exists():
        for bp in sorted([d for d in BLUEPRINTS_DIR.iterdir() if d.is_dir()]):
            report["blueprints"].append(audit_blueprint(bp, defined_models, mail_defs))

    # Write JSON/MD
    (ROOT / "audit_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Pretty Markdown
    md = ["# PittState-Connect Audit Report", ""]
    md.append("## Summary")
    md.append(f"- Models defined: {len(defined_models)}")
    md.append(f"- Mail utils exported: {', '.join(sorted(mail_defs)) or '—'}")
    if mail_used - mail_defs:
        md.append(f"- ⚠ Missing mail utils: {', '.join(sorted(mail_used - mail_defs))}")
    md.append("")
    md.append("## Blueprints")
    for bp in report["blueprints"]:
        md.append(f"### `{bp['name']}` — **{bp['status']}**")
        if bp["problems"]:
            md.append(f"- Problems: {', '.join(bp['problems'])}")
        md.append(f"- routes.py: {', '.join(bp['routes_files'])}")
        md.append(f"- blueprint vars: {', '.join(bp['blueprint_vars']) or '—'}")
        md.append(f"- url_prefix: `{bp['url_prefix'] or '—'}`")
        md.append(f"- routes: {', '.join(bp['routes']) or '—'}")
        md.append(f"- models used: {', '.join(bp['models_used']) or '—'}")
        if bp["missing_models"]:
            md.append(f"- ⚠ missing models: {', '.join(bp['missing_models'])}")
        md.append(f"- templates used: {', '.join(bp['templates_used']) or '—'}")
        if bp["missing_templates"]:
            md.append(f"- ⚠ missing templates: {', '.join(bp['missing_templates'])}")
        md.append("")
    Path("audit_report.md").write_text("\n".join(md), encoding="utf-8")
    print("✅ Wrote audit_report.md and audit_report.json")

if __name__ == "__main__":
    main()
