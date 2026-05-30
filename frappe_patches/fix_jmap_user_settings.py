"""
Patch: frappe/mail User Settings - change identity validation from throw to msgprint.

When a user first sets up their mail settings, the JMAP identity may not yet exist in
Stalwart. The original code throws an error preventing saving. This patch changes it to
a non-blocking msgprint so the User Settings document can be saved and the identity
will be created on first use.
"""
import pathlib

p = pathlib.Path(
    "/home/frappe/frappe-bench/apps/mail/mail/client/doctype/user_settings/user_settings.py"
)
if not p.exists():
    print("SKIP: user_settings.py not found (mail app not installed?)")
    raise SystemExit(0)

content = p.read_text()

old = '''        if not identity_service.get_identity_id_by_email(self.default_outgoing_email):
            frappe.throw(
                _("Default Outgoing Email {0} is not found in the identities of the JMAP account.").format(frappe.bold(self.default_outgoing_email))
            )'''

new = '''        if not identity_service.get_identity_id_by_email(self.default_outgoing_email):
            frappe.msgprint(
                _("Default Outgoing Email {0} is not yet found in the identities of the JMAP account. It will be created on first use.").format(frappe.bold(self.default_outgoing_email)),
                alert=True
            )'''

if "alert=True" in content:
    print("SKIP: user_settings.py already patched")
    raise SystemExit(0)

if old not in content:
    print(f"WARNING: exact target string not found in {p}, trying fuzzy match...")
    # Try to find and show context around the throw
    import re
    m = re.search(r"if not identity_service\.get_identity_id_by_email.*?frappe\.throw.*?\)", content, re.DOTALL)
    if m:
        print("Found similar block:", repr(m.group()))
    else:
        print("No similar block found either. File may have changed upstream.")
    raise SystemExit(1)

p.write_text(content.replace(old, new, 1))
print(f"PATCHED: {p} - identity validation changed from throw to msgprint")
