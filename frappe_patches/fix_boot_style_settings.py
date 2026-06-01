"""
Patch: Guard against missing 'Style Settings' DocType in ERPNext boot.py.

ERPNext v15 boot.py references the 'Style Settings' DocType which no longer
exists in newer Frappe versions. This patch wraps the call in a try/except
so the boot session doesn't 500 when the DocType is absent.
"""

import re
import sys


def patch_boot_py():
    path = None
    for p in sys.path:
        candidate = p + "/erpnext/startup/boot.py"
        try:
            open(candidate).read()
            path = candidate
            break
        except FileNotFoundError:
            pass

    if path is None:
        # Try direct path (frappe_docker layout)
        import glob
        matches = glob.glob(
            "/home/frappe/frappe-bench/apps/erpnext/erpnext/startup/boot.py"
        )
        if matches:
            path = matches[0]

    if path is None:
        print("fix_boot_style_settings: boot.py not found, skipping")
        return

    content = open(path).read()

    old = 'bootinfo.custom_css = frappe.db.get_value("Style Settings", None, "custom_css") or ""'
    new = (
        'try:\n'
        '\t\tbootinfo.custom_css = frappe.db.get_value("Style Settings", None, "custom_css") or ""\n'
        '\texcept Exception:\n'
        '\t\tbootinfo.custom_css = ""'
    )

    if old not in content:
        print("fix_boot_style_settings: already patched or line not found, skipping")
        return

    content = content.replace(old, new)
    open(path, "w").write(content)
    print("fix_boot_style_settings: patched boot.py successfully")


patch_boot_py()
