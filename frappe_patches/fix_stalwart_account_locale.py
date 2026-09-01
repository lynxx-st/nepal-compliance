"""Patch Frappe Mail's Stalwart account locale for Stalwart 0.16+.

Frappe Mail currently serializes the default locale as ``en_US``. Stalwart's
management API expects the BCP 47 spelling ``en-US`` and rejects account
creation with ``invalidPatch`` when it receives the underscore form.
"""

from __future__ import annotations

import ast
from pathlib import Path


path = Path("/home/frappe/frappe-bench/apps/mail/mail/stalwart/account.py")
if not path.exists():
    print("SKIP: Stalwart account model not found (mail app not installed?)")
    raise SystemExit(0)

content = path.read_text(encoding="utf-8")
old = '\tlocale: str = "en_US"'
new = '\tlocale: str = "en-US"'

if new in content:
    print("SKIP: Stalwart account locale is already compatible")
    raise SystemExit(0)

if old not in content:
    raise SystemExit(f"ERROR: expected locale declaration not found in {path}")

patched = content.replace(old, new, 1)
ast.parse(patched, filename=str(path))
path.write_text(patched, encoding="utf-8")
print(f"PATCHED: {path} - normalized default locale to en-US")
