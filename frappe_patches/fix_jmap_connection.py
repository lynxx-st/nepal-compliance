"""
Patch: frappe/mail JMAP connection - disable TLS verification for internal Docker hostname.

Stalwart returns a JMAP session URL using its container hostname (e.g. https://d9218690d0e3/...)
which has a self-signed cert. This patch disables SSL verify for the internal JMAP session
so ERPNext mail can talk to Stalwart over Docker's internal network.
"""
import pathlib

p = pathlib.Path("/home/frappe/frappe-bench/apps/mail/mail/jmap/connection.py")
if not p.exists():
    print("SKIP: connection.py not found (mail app not installed?)")
    raise SystemExit(0)

content = p.read_text()
old = "self.__session = requests.Session()"
new = "self.__session = requests.Session()\n        self.__session.verify = False  # allow self-signed cert from Stalwart internal Docker hostname"

if "self.__session.verify = False" in content:
    print("SKIP: connection.py already patched")
    raise SystemExit(0)

if old not in content:
    print(f"ERROR: target string not found in {p}")
    print("First 500 chars:", content[:500])
    raise SystemExit(1)

p.write_text(content.replace(old, new, 1))
print(f"PATCHED: {p} - jmap ssl verify=False for internal docker hostname")
