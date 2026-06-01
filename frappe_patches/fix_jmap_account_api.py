"""
Patch: frappe/mail account API - handle missing JMAP settings gracefully.

When a user opens /mail without JMAP configured, the original code throws
a ValidationError (500/417) crashing the entire page. This patch wraps the
User Account fetch in a try/except so the API returns an empty account list
plus jmap_setup_required=True instead of crashing.

The frontend can use the jmap_setup_required flag to show a setup prompt.
"""
import pathlib
import ast

p = pathlib.Path("/home/frappe/frappe-bench/apps/mail/mail/api/account.py")
if not p.exists():
    print("SKIP: account.py not found (mail app not installed?)")
    raise SystemExit(0)

content = p.read_text()

if "jmap_setup_required" in content:
    print("SKIP: account.py already patched")
    raise SystemExit(0)

old = '\tdata.accounts = frappe.get_all("User Account", filters={"user": user})'
new = '''\ttry:
\t\tdata.accounts = frappe.get_all("User Account", filters={"user": user})
\t\tdata.jmap_setup_required = False
\texcept Exception:
\t\tdata.accounts = []
\t\tdata.jmap_setup_required = True
\t\tdata.jmap_setup_url = "/desk/user-settings/new"'''

if old not in content:
    print(f"ERROR: target line not found in {p}")
    idx = content.find("User Account")
    if idx >= 0:
        print("Context:", repr(content[max(0, idx-50):idx+100]))
    raise SystemExit(1)

fixed = content.replace(old, new, 1)

try:
    ast.parse(fixed)
except SyntaxError as e:
    print(f"ERROR: patched file has syntax error: {e}")
    raise SystemExit(1)

p.write_text(fixed)
print(f"PATCHED: {p} - JMAP not configured error handled gracefully")
