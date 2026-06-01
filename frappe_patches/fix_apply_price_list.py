"""
Patch: Add 'ctx' parameter alias to apply_price_list in ERPNext.

ERPNext v16 frontend sends {ctx: ..., doc: ...} but the Python function
still expects {args: ..., as_doc: ...}. This adds ctx as an alias for args
so both old and new JS callers work without error.
"""

import glob


def patch_get_item_details():
    matches = glob.glob(
        "/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/get_item_details.py"
    )
    if not matches:
        print("fix_apply_price_list: get_item_details.py not found, skipping")
        return

    path = matches[0]
    content = open(path).read()

    old = "def apply_price_list(args, as_doc=False, doc=None):"
    new = (
        "def apply_price_list(args=None, as_doc=False, doc=None, ctx=None):\n"
        "\tif ctx is not None and args is None:\n"
        "\t\targs = ctx"
    )

    if old not in content:
        print("fix_apply_price_list: already patched or signature changed, skipping")
        return

    content = content.replace(old, new, 1)
    open(path, "w").write(content)
    print("fix_apply_price_list: patched apply_price_list to accept ctx alias")


patch_get_item_details()
