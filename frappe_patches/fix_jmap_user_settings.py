"""
Patch: frappe/mail User Settings - change identity validation from throw to msgprint.

When a user first sets up their mail settings, the JMAP identity may not yet exist in
Stalwart. The original code throws an error preventing saving. This patch changes it to
a non-blocking msgprint so the User Settings document can be saved and the identity
will be created on first use.

Uses regex replacement to handle any indentation style (tabs or spaces).
"""
import pathlib
import re

p = pathlib.Path(
    "/home/frappe/frappe-bench/apps/mail/mail/client/doctype/user_settings/user_settings.py"
)
if not p.exists():
    print("SKIP: user_settings.py not found (mail app not installed?)")
    raise SystemExit(0)

content = p.read_text()

if "alert=True" in content:
    print("SKIP: user_settings.py already patched")
    raise SystemExit(0)

# Match the entire block: if not identity_service... frappe.throw(...) with any indentation
pattern = re.compile(
    r'([ \t]*)if not identity_service\.get_identity_id_by_email\(self\.default_outgoing_email\):\s*\n'
    r'[ \t]*frappe\.throw\(\s*\n'
    r'.*?"Default Outgoing Email \{0\} is not found in the identities of the JMAP account\.".*?\n'
    r'[ \t]*\)\s*\n'
    r'[ \t]*\)',
    re.DOTALL
)

m = pattern.search(content)
if not m:
    # Try a simpler pattern as fallback
    pattern2 = re.compile(
        r'([ \t]*)if not identity_service\.get_identity_id_by_email\(self\.default_outgoing_email\):.*?frappe\.throw\(.*?\)',
        re.DOTALL
    )
    m = pattern2.search(content)

if not m:
    print(f"ERROR: could not find identity validation block in {p}")
    print("File content around 'get_identity_id_by_email':")
    idx = content.find("get_identity_id_by_email")
    if idx >= 0:
        print(repr(content[max(0, idx-100):idx+300]))
    raise SystemExit(1)

indent = m.group(1)
replacement = (
    f"{indent}if not identity_service.get_identity_id_by_email(self.default_outgoing_email):\n"
    f"{indent}\tfrappe.msgprint(\n"
    f"{indent}\t\t_(\n"
    f'{indent}\t\t\t"Default Outgoing Email {{0}} is not yet found in the identities of the JMAP account. It will be created on first use."\n'
    f"{indent}\t\t).format(frappe.bold(self.default_outgoing_email)),\n"
    f"{indent}\t\talert=True,\n"
    f"{indent}\t)"
)

new_content = content[:m.start()] + replacement + content[m.end():]
p.write_text(new_content)
print(f"PATCHED: {p} - identity validation changed from throw to msgprint")
