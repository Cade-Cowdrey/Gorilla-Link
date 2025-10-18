#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bp_dir = ROOT / "blueprints"

for d in sorted([x for x in bp_dir.iterdir() if x.is_dir()]):
    rp = d / "routes.py"
    if not rp.exists():
        print(f"❌ {d.name}: routes.py missing")
        continue
    s = rp.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'([a-zA-Z_]\w*)\s*=\s*Blueprint\(\s*[\'"]([a-zA-Z0-9_\-]+)[\'"]', s)
    var = m.group(1) if m else None
    expected = f"{d.name}_bp"
    if var != expected:
        print(f"⚠️ {d.name}: export var is '{var}', expected '{expected}'")
    else:
        print(f"✅ {d.name}: export '{expected}' ok")
