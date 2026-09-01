"""Keep the Frappe Mail domain selector inside the Add Member dialog."""

from pathlib import Path


component = Path(
    "/home/frappe/frappe-bench/apps/mail/frontend/src/components/Modals/AddMemberModal.vue"
)

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
