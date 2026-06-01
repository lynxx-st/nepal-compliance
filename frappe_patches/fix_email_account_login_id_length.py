"""
Patch: Expand Email Account login_id field to 255 chars.

Oracle Cloud SMTP user IDs are ~163 characters, exceeding the default
140-char limit on the login_id (Alternative Email ID) field in the
Email Account doctype. This patch updates both the DocType JSON and the
MariaDB column so Frappe stops truncating Oracle SMTP credentials.
"""

import glob
import json


def patch_email_account_json():
    """Expand login_id maxlength in the Email Account doctype JSON."""
    matches = glob.glob(
        "/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype"
        "/email_account/email_account.json"
    )
    if not matches:
        print("fix_email_account_login_id_length: email_account.json not found, skipping")
        return

    path = matches[0]
    with open(path) as f:
        doctype = json.load(f)

    changed = False
    for field in doctype.get("fields", []):
        if field.get("fieldname") == "login_id":
            if field.get("length", 0) < 255:
                field["length"] = 255
                changed = True
                break

    if not changed:
        print("fix_email_account_login_id_length: already 255 or field not found, skipping")
        return

    with open(path, "w") as f:
        json.dump(doctype, f, indent=1)
    print("fix_email_account_login_id_length: set login_id length=255 in doctype JSON")


patch_email_account_json()
