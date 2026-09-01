"""Allow Frappe Mail to reconcile an exact existing Stalwart mailbox.

Account creation can be interrupted after Stalwart succeeds but before the
Frappe User and User Settings are committed. A retry then fails with a primary
key violation. For an exact email match, update the existing mailbox password
and let the normal Frappe provisioning flow continue. A same-name account on a
different domain remains an error.
"""

from __future__ import annotations

import ast
from pathlib import Path


path = Path("/home/frappe/frappe-bench/apps/mail/mail/stalwart/__init__.py")
if not path.exists():
    print("SKIP: Stalwart integration not found (mail app not installed?)")
    raise SystemExit(0)

content = path.read_text(encoding="utf-8")
marker = "existing_accounts = account_service.get_all"
if marker in content:
    print("SKIP: existing Stalwart account reconciliation is already patched")
    raise SystemExit(0)

old = "\tAccountService().create(account)"
new = '''\taccount_service = AccountService()
\texisting_accounts = account_service.get_all(
\t\t{"name": name}, fields=["id", "emailAddress"]
\t)
\tif existing_accounts:
\t\texisting_account = existing_accounts[0]
\t\texpected_email = f"{name}@{domain}".lower()
\t\tif existing_account.get("emailAddress", "").lower() != expected_email:
\t\t\tfrappe.throw(_("Account {0} already exists for another domain.").format(name))
\t\taccount_service.update_password(existing_account["id"], password)
\telse:
\t\taccount_service.create(account)'''

if old not in content:
    raise SystemExit(f"ERROR: expected account creation call not found in {path}")

patched = content.replace(old, new, 1)
ast.parse(patched, filename=str(path))
path.write_text(patched, encoding="utf-8")
print(f"PATCHED: {path} - exact existing mailboxes are reconciled")
