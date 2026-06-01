"""
Patch: PWA setup for ERPNext desk + fix frappe/mail manifest scope.

Two changes:
A. Patches desk.html to add <link rel="manifest"> and service worker registration
   so the ERPNext desk becomes installable as a PWA on phones.

B. Fixes the frappe/mail manifest.webmanifest scope from "/assets/mail/frontend/"
   to "/mail" so it matches start_url and Chrome doesn't show the URL bar.
"""
import pathlib
import json

# ── A. Patch desk.html ────────────────────────────────────────────────────────

desk = pathlib.Path("/home/frappe/frappe-bench/apps/frappe/frappe/www/desk.html")
if not desk.exists():
    print("SKIP: desk.html not found")
else:
    content = desk.read_text()

    manifest_link = '<link rel="manifest" href="/manifest.webmanifest">\n\t<link rel="apple-touch-icon" href="/assets/nepal_compliance/icon/app-icon.svg">'
    sw_script = '\n\t<script>if("serviceWorker" in navigator) { navigator.serviceWorker.register("/sw.js", {scope: "/"}).catch(function(){}); }</script>'

    changed = False

    # Add manifest link if not already there
    if 'rel="manifest"' not in content:
        # Insert after the mobile-web-app-capable meta tag
        target = '<meta name="mobile-web-app-capable" content="yes">'
        if target in content:
            content = content.replace(target, target + "\n\t" + manifest_link)
            changed = True
            print("PATCHED: desk.html - added manifest link and apple-touch-icon")
        else:
            # Fallback: insert before </head>
            content = content.replace("</head>", "\t" + manifest_link + "\n</head>")
            changed = True
            print("PATCHED: desk.html - added manifest link (fallback position)")
    else:
        print("SKIP: desk.html manifest link already present")

    # Add service worker registration before </body>
    if "serviceWorker" not in content:
        content = content.replace("</body>", sw_script + "\n</body>")
        changed = True
        print("PATCHED: desk.html - added service worker registration")
    else:
        print("SKIP: desk.html SW registration already present")

    if changed:
        desk.write_text(content)


# ── B. Fix mail manifest scope ────────────────────────────────────────────────

mail_manifest = pathlib.Path(
    "/home/frappe/frappe-bench/apps/mail/mail/public/frontend/manifest.webmanifest"
)
if not mail_manifest.exists():
    print("SKIP: mail manifest not found")
else:
    try:
        data = json.loads(mail_manifest.read_text())
        if data.get("scope") == "/assets/mail/frontend/":
            data["scope"] = "/mail"
            mail_manifest.write_text(json.dumps(data, indent=2))
            print("PATCHED: mail manifest.webmanifest - scope fixed to /mail")
        elif data.get("scope") == "/mail":
            print("SKIP: mail manifest scope already correct")
        else:
            print(f"INFO: mail manifest scope is '{data.get('scope')}' - leaving unchanged")
    except json.JSONDecodeError as e:
        print(f"ERROR: could not parse mail manifest: {e}")
