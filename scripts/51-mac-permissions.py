"""Give the re-signed packages the platform SELinux identity.

mac_permissions.xml maps a signer certificate to a seinfo value. The ROM's copy only knows
the original SandroidTeam certificate, so every re-signed package falls back to seinfo
"default"; seapp_contexts has no entry for uid 1000 with that seinfo, and the process dies in
selinux_android_setcontext before it can start ("No match for app with uid 1000, seinfo
default"). Adding our certificate with seinfo "platform" restores the previous identity.

Usage: python scripts/51-mac-permissions.py <cert.der> [--dry-run]
Writes: work/mac_permissions.xml
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "work", "mac_permissions.xml.orig")
OUT = os.path.join(ROOT, "work", "mac_permissions.xml")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    der = open(sys.argv[1], "rb").read()
    sig = der.hex().upper()
    xml = open(SRC, encoding="iso-8859-1").read()
    if sig in xml:
        print("certificate already present")
        return 0
    entry = f'<signer signature="{sig}"><seinfo value="platform"/></signer>'
    marker = "<policy>"
    if marker not in xml:
        raise SystemExit("unexpected mac_permissions.xml layout")
    xml = xml.replace(marker, marker + entry, 1)
    if "--dry-run" in sys.argv:
        print(f"would insert {len(entry)} chars after <policy>")
        return 0
    with open(OUT, "w", encoding="iso-8859-1", newline="") as fh:
        fh.write(xml)
    print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes), signer {sig[:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
