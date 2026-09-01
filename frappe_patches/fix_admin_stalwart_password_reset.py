"""Allow administrators to synchronize Frappe Mail user password resets.

Frappe Mail's password hook previously resolved the target mailbox through a
JMAP connection.  That lookup applies end-user permissions, so a System
Manager resetting another user's password was rejected before Stalwart could
be updated.  Resolve the exact Stalwart account through the configured mail
identity instead; the surrounding Frappe User update remains responsible for
authorization.
"""

from __future__ import annotations

import ast
from pathlib import Path


path = Path("/home/frappe/frappe-bench/apps/mail/mail/stalwart/__init__.py")
if not path.exists():
    print("SKIP: Stalwart integration not found (mail app not installed?)")
    raise SystemExit(0)

content = path.read_text(encoding="utf-8")
marker = "mailbox identity does not match the Stalwart account"
if marker in content:
    print("SKIP: administrator Stalwart password reset is already patched")
    raise SystemExit(0)

old = '''\taccount_id = get_user_personal_account(user, "id", raise_exception=False)
\tAccountService().update_password(account_id, new_password)'''
new = '''\tusername = frappe.db.get_value("User Settings", {"user": user}, "username")
\tif not username or "@" not in username:
\t\tfrappe.throw(_("User {0} does not have a configured mail account.").format(frappe.bold(user)))

\taccount_name = username.rsplit("@", 1)[0]
\taccounts = AccountService().get_all({"name": account_name}, fields=["id", "emailAddress"])
\tif not accounts:
\t\tfrappe.throw(_("Mail account {0} was not found on the server.").format(frappe.bold(username)))

\taccount = accounts[0]
\t# The mailbox identity does not match the Stalwart account: refuse to update
\t# a same-local-part account belonging to another hosted domain.
\tif account.get("emailAddress", "").lower() != username.lower():
\t\tfrappe.throw(_("Mail account {0} belongs to another domain.").format(frappe.bold(account_name)))

\tAccountService().update_password(account["id"], new_password)'''

if old not in content:
    raise SystemExit(f"ERROR: expected Stalwart password update block not found in {path}")

patched = content.replace(old, new, 1)
ast.parse(patched, filename=str(path))
path.write_text(patched, encoding="utf-8")
print(f"PATCHED: {path} - administrator password resets now synchronize safely")
