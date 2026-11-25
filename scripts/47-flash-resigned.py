"""Flash the re-signed /system APKs from work/resigned and clear the stale oat files.

Run only from TWRP. Every APK is pushed to the path it came from, given the system_file
label, and its oat directory is removed so ART recompiles against the new certificate.
/data/system/packages.xml keeps the old android.uid.system signature set, which would make
PackageManagerService reject every member with INSTALL_FAILED_SHARED_USER_INCOMPATIBLE, so
that one <signatures> block is dropped and PMS adopts the new certificate on the next scan.

Usage: python scripts/47-flash-resigned.py --confirm
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
RESIGNED = os.path.join(ROOT, "work", "resigned")
BACKUP = os.path.join(ROOT, "backup")


def adb(*args, **kw):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True,
                          errors="replace", **kw)


def sh(cmd):
    r = adb("shell", cmd)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    if "--confirm" not in sys.argv:
        print("refusing to flash without --confirm")
        return 2

    rc, out = sh("getprop ro.twrp.version")
    if not out.strip():
        print("device is not in TWRP; aborting")
        return 1
    print("TWRP", out.strip())

    apks = []
    for dirpath, _, files in os.walk(RESIGNED):
        for f in sorted(files):
            if f.endswith(".apk"):
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, RESIGNED).replace("\\", "/")
                apks.append((rel, full))
    apks.sort()
    print(f"re-signed APKs to flash: {len(apks)}")

    rc, out = sh("mount /system 2>&1; mount -o rw,remount /system 2>&1; echo done")
    print("mount:", out.strip().splitlines()[-1] if out.strip() else "?")

    # packages.xml: keep a copy on the host before touching it.
    os.makedirs(BACKUP, exist_ok=True)
    adb("pull", "/data/system/packages.xml", os.path.join(BACKUP, "packages.xml"))
    print("packages.xml backed up")

    failed = []
    for rel, full in apks:
        target = "/system/" + rel
        r = adb("push", full, target)
        if r.returncode != 0:
            failed.append((rel, "push: " + (r.stderr or r.stdout).strip()[:160]))
            continue
        oat = target.rsplit("/", 1)[0] + "/oat"
        rc, out = sh(f"chmod 644 {target}; chown 0:0 {target}; "
                     f"chcon u:object_r:system_file:s0 {target}; rm -rf {oat}; echo ok")
        if "ok" not in out:
            failed.append((rel, "post: " + out.strip()[:160]))
    print(f"flashed: {len(apks) - len(failed)}   failed: {len(failed)}")
    for rel, why in failed:
        print("  FAIL", rel, why)

    # Drop every stored signature set so PMS re-reads them from the new APKs. Leaving them
    # would make verifySignaturesLP throw for each re-signed package, and the recovery path
    # then compares against the shared user's old certificate and fails the whole scan.
    rc, out = sh("grep -c '<sigs count=' /data/system/packages.xml")
    print("sigs blocks before:", out.strip())
    rc, out = sh("sed -i '/<sigs count=/,/<\\/sigs>/d' /data/system/packages.xml; "
                 "grep -c '<sigs count=' /data/system/packages.xml")
    print("sigs blocks after:", out.strip())

    sh("sync")
    print("done; reboot to system to verify")


if __name__ == "__main__":
    sys.exit(main())
