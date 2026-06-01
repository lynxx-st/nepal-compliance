"""
Patch: Guard against missing 'Style Settings' DocType in ERPNext boot.py.

ERPNext v16 boot.py still references the 'Style Settings' DocType which
no longer exists in newer Frappe. Uses frappe.db.table_exists() to check
before querying, avoiding the DoesNotExistError that crashes boot.
"""

import glob


def patch_boot_py():
    path = None
    matches = glob.glob("/home/frappe/frappe-bench/apps/erpnext/erpnext/startup/boot.py")
    if matches:
        path = matches[0]

    if path is None:
        print("fix_boot_style_settings: boot.py not found, skipping")
        return

    content = open(path).read()

    old = '\tbootinfo.custom_css = frappe.db.get_value("Style Settings", None, "custom_css") or ""\n'
    new = (
        '\tif frappe.db.table_exists("tabStyle Settings"):\n'
        '\t\tbootinfo.custom_css = frappe.db.get_value("Style Settings", None, "custom_css") or ""\n'
        '\telse:\n'
        '\t\tbootinfo.custom_css = ""\n'
    )

    if old not in content:
        print("fix_boot_style_settings: already patched or line not found, skipping")
        return

    content = content.replace(old, new)
    open(path, "w").write(content)
    print("fix_boot_style_settings: patched boot.py with table_exists guard")


patch_boot_py()
