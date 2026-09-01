"""Keep the Frappe Mail domain selector inside the Add Member dialog."""

import os
from pathlib import Path


bench_path = Path(os.environ.get("FRAPPE_BENCH_PATH", "/home/frappe/frappe-bench"))
component = bench_path / "apps/mail/frontend/src/components/Modals/AddMemberModal.vue"
public_assets = bench_path / "apps/mail/mail/public/frontend/assets"

if not component.exists():
    print("SKIP: Frappe Mail AddMemberModal.vue not found")
else:
    content = component.read_text(encoding="utf-8")
    fixed_marker = 'grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]'

    if fixed_marker in content:
        print("SKIP: Frappe Mail member domain layout already fixed")
    else:
        original = '''\t\t\t\t<div class="flex items-center justify-between">
\t\t\t\t\t<FormControl
\t\t\t\t\t\tv-model="accountRequest.username"
\t\t\t\t\t\t:label="__('Username')"
\t\t\t\t\t\tplaceholder="johndoe"
\t\t\t\t\t\tclass="w-full"
\t\t\t\t\t/>
\t\t\t\t\t<FeatherIcon
\t\t\t\t\t\tclass="text-ink-gray-3 mx-2.5 mb-1.5 mt-auto h-4 w-4"
\t\t\t\t\t\tname="at-sign"
\t\t\t\t\t/>
\t\t\t\t\t<FormControl
\t\t\t\t\t\tv-model="accountRequest.domain"
\t\t\t\t\t\ttype="combobox"
\t\t\t\t\t\t:label="__('Domain')"
\t\t\t\t\t\tplaceholder="yourdomain.com"
\t\t\t\t\t\tclass="w-full"
\t\t\t\t\t\t:options="domains.data"
\t\t\t\t\t\t:open-on-click="true"
\t\t\t\t\t/>
\t\t\t\t</div>'''
        replacement = '''\t\t\t\t<div
\t\t\t\t\tclass="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-end"
\t\t\t\t>
\t\t\t\t\t<FormControl
\t\t\t\t\t\tv-model="accountRequest.username"
\t\t\t\t\t\t:label="__('Username')"
\t\t\t\t\t\tplaceholder="johndoe"
\t\t\t\t\t\tclass="min-w-0"
\t\t\t\t\t/>
\t\t\t\t\t<FeatherIcon
\t\t\t\t\t\tclass="text-ink-gray-3 mx-2.5 mb-1.5 h-4 w-4"
\t\t\t\t\t\tname="at-sign"
\t\t\t\t\t/>
\t\t\t\t\t<FormControl
\t\t\t\t\t\tv-model="accountRequest.domain"
\t\t\t\t\t\ttype="combobox"
\t\t\t\t\t\t:label="__('Domain')"
\t\t\t\t\t\tplaceholder="yourdomain.com"
\t\t\t\t\t\tclass="min-w-0"
\t\t\t\t\t\t:options="domains.data"
\t\t\t\t\t\t:open-on-click="true"
\t\t\t\t\t/>
\t\t\t\t</div>'''

        if original not in content:
            raise SystemExit("ERROR: unexpected Frappe Mail Add Member layout")

        component.write_text(content.replace(original, replacement, 1), encoding="utf-8")
        print("PATCHED: Frappe Mail Add Member domain selector layout")

# The custom image is assembled after upstream has already built its frontend.
# Patch the matching compiled chunk as well, avoiding another full asset build.
compiled_original = 'class:"flex items-center justify-between"'
compiled_replacement = (
    'style:{display:"grid","grid-template-columns":'
    '"minmax(0,1fr) auto minmax(0,1fr)","align-items":"end"}'
)
compiled_found = False

for asset in public_assets.glob("MembersView-*.js"):
    bundled = asset.read_text(encoding="utf-8")
    if "yourdomain.com" not in bundled:
        continue

    compiled_found = True
    if compiled_replacement in bundled:
        print(f"SKIP: compiled member layout already fixed in {asset.name}")
    elif compiled_original in bundled:
        asset.write_text(
            bundled.replace(compiled_original, compiled_replacement, 1), encoding="utf-8"
        )
        print(f"PATCHED: compiled Frappe Mail member layout in {asset.name}")
    else:
        raise SystemExit(f"ERROR: unexpected compiled member layout in {asset.name}")

if public_assets.exists() and not compiled_found:
    raise SystemExit("ERROR: compiled Frappe Mail MembersView asset not found")
