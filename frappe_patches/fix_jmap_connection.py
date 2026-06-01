"""
Patch: frappe/mail - disable TLS verification for internal Docker hostname connections.

Stalwart returns a JMAP session URL using its container hostname (e.g. https://d9218690d0e3/...)
which has a self-signed cert. This patch disables SSL verify in ALL session objects
so ERPNext mail can talk to Stalwart over Docker's internal network without SSL errors.

Patches two files:
  - mail/jmap/connection.py  (JMAP client sessions)
  - mail/backend.py          (HTTP backend sessions)
"""
import pathlib, re


def patch_session(path_str: str) -> None:
    p = pathlib.Path(path_str)
    if not p.exists():
        print(f"SKIP: {p.name} not found")
        return

    content = p.read_text()
    if "self.__session.verify = False" in content:
        print(f"SKIP: {p.name} already patched")
        return

    m = re.search(r'([ \t]*)self\.__session = requests\.Session\(\)', content)
    if not m:
        print(f"ERROR: Session() not found in {p.name}")
        return

    indent = m.group(1)
    old = "self.__session = requests.Session()"
    new = (
        f"self.__session = requests.Session()\n"
        f"{indent}self.__session.verify = False  # allow self-signed cert from Stalwart internal Docker hostname"
    )
    p.write_text(content.replace(old, new, 1))
    print(f"PATCHED: {p} - added verify=False")


patch_session("/home/frappe/frappe-bench/apps/mail/mail/jmap/connection.py")
patch_session("/home/frappe/frappe-bench/apps/mail/mail/backend.py")
