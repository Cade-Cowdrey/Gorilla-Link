#!/usr/bin/env python3
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
changed = 0
for p in (ROOT/"blueprints").rglob("*.py"):
    s = p.read_text(encoding="utf-8", errors="ignore")
    ns = re.sub(r"from\s+\.\.+\s*models\s+import", "from models import", s)
    ns = re.sub(r"from\s+\.\.+\s*utils\.mail_util\s+import", "from utils.mail_util import", ns)
    if ns != s:
        p.write_text(ns, encoding="utf-8")
        print("fixed:", p)
        changed += 1
print(f"✅ Updated {changed} files")
