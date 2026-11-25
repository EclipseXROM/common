"""Work out which /system packages must be re-signed together with Settings.apk.

Signature-level permissions are granted only when the requesting package's certificate
matches the certificate of the package that *defines* the permission. Re-signing
framework-res.apk with a new key therefore revokes every signature permission from every
package that is not re-signed in the same pass, so the set has to be computed, not guessed.

Usage: python scripts/45-signature-dependents.py
Writes: work/signature-dependents.json
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AAPT = os.path.join(ROOT, "tools", "sdk", "build-tools", "30.0.3", "aapt.exe")
APKS = os.path.join(ROOT, "backup", "system-apks")
OUT = os.path.join(ROOT, "work", "signature-dependents.json")

# protectionLevel base values (PackageManager.PermissionInfo)
BASE_NORMAL, BASE_DANGEROUS, BASE_SIGNATURE, BASE_SIGNATURE_OR_SYSTEM = 0, 1, 2, 3


def xmltree(apk, inner):
    r = subprocess.run([AAPT, "dump", "xmltree", apk, inner],
                       capture_output=True, text=True, errors="replace")
    return r.stdout.splitlines()


def permissions(apk):
    """name -> protectionLevel base value, for every <permission> in the manifest."""
    lines = xmltree(apk, "AndroidManifest.xml")
    out = {}
    for i, line in enumerate(lines):
        if not line.strip().startswith("E: permission "):
            continue
        indent = len(line) - len(line.lstrip())
        name = level = None
        for j in range(i + 1, min(i + 10, len(lines))):
            s = lines[j]
            if len(s) - len(s.lstrip()) <= indent:
                break
            m = re.search(r'android:name\(0x01010003\)="([^"]+)"', s)
            if m and name is None:
                name = m.group(1)
            m = re.search(r'android:protectionLevel\(0x01010009\)=\(type 0x1[01]\)0x([0-9a-f]+)', s)
            if m:
                level = int(m.group(1), 16) & 0xf
        if name:
            out[name] = level
    return out


def requested(apk):
    r = subprocess.run([AAPT, "dump", "permissions", apk],
                       capture_output=True, text=True, errors="replace")
    return set(re.findall(r"^uses-permission: name='([^']+)'", r.stdout, re.M))


def main():
    definers = {}
    for apk in ("framework/framework-res.apk", "framework/org.cyanogenmod.platform-res.apk"):
        p = os.path.join(APKS, apk)
        for name, level in permissions(p).items():
            if level in (BASE_SIGNATURE, BASE_SIGNATURE_OR_SYSTEM):
                definers[name] = (level, apk)
    print(f"signature-level permissions defined: {len(definers)}")

    rows = []
    for dirpath, _, files in os.walk(APKS):
        for f in sorted(files):
            if not f.endswith(".apk"):
                continue
            apk = os.path.join(dirpath, f)
            rel = os.path.relpath(apk, APKS).replace("\\", "/")
            hit = sorted(requested(apk) & set(definers))
            rows.append({"apk": rel, "signature_permissions": hit, "count": len(hit)})

    rows.sort(key=lambda r: (-r["count"], r["apk"]))
    dependents = [r for r in rows if r["count"]]
    print(f"packages holding signature permissions: {len(dependents)} of {len(rows)}")
    for r in dependents:
        print(f"  {r['count']:3}  {r['apk']}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"definers": {k: v[1] for k, v in definers.items()},
                   "packages": rows}, fh, indent=1)
    print("written", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
