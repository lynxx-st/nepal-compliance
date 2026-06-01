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

# Find the start of the `if not identity_service...` block
start_pat = re.compile(
    r'([ \t]*)if not identity_service\.get_identity_id_by_email\(self\.default_outgoing_email\):'
)
m = start_pat.search(content)
if not m:
    print(f"ERROR: could not find identity validation block in {p}")
    raise SystemExit(1)

indent = m.group(1)
block_start = m.start()

# Find `frappe.throw(` after the if line
throw_idx = content.find("frappe.throw(", block_start)
if throw_idx == -1:
    print(f"ERROR: frappe.throw( not found after if block in {p}")
    raise SystemExit(1)

# Walk forward tracking paren depth to find the matching closing paren
depth = 0
i = throw_idx + len("frappe.throw(") - 1  # position of the opening '('
while i < len(content):
    if content[i] == '(':
        depth += 1
    elif content[i] == ')':
        depth -= 1
        if depth == 0:
            block_end = i + 1  # character after the final ')'
            break
    i += 1
else:
    print(f"ERROR: could not find matching ')' for frappe.throw( in {p}")
    raise SystemExit(1)

replacement = (
    f"{indent}if not identity_service.get_identity_id_by_email(self.default_outgoing_email):\n"
    f"{indent}\tfrappe.msgprint(\n"
    f"{indent}\t\t_(\n"
    f'{indent}\t\t\t"Default Outgoing Email {{0}} is not yet found in the identities of the JMAP account. It will be created on first use."\n'
    f"{indent}\t\t).format(frappe.bold(self.default_outgoing_email)),\n"
    f"{indent}\t\talert=True,\n"
    f"{indent}\t)"
)

new_content = content[:block_start] + replacement + content[block_end:]

# Verify syntax before writing
import ast
try:
    ast.parse(new_content)
except SyntaxError as e:
    print(f"ERROR: patched file has syntax error: {e}")
    raise SystemExit(1)

p.write_text(new_content)
print(f"PATCHED: {p} - identity validation changed from throw to msgprint")
