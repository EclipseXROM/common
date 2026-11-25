"""Push the odex trees back into /system after a zip flash.

The ROM ships stripped APKs (no classes.dex), so ART can only load them through the matching
.odex. The installer deletes every oat directory belonging to a re-signed package, which is
correct for stale odex but leaves the packages unloadable unless the trees are restored.
work/oat-tree and work/framework-oat hold them, extracted from the ROM image by
scripts/49-ext4-extract.py and scripts/50-restore-oat.py.

Run only from TWRP with /system mounted read-write.

Usage: python scripts/54-restore-oat-system.py [--confirm]
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
TREE = os.path.join(ROOT, "work", "oat-tree")
FRAMEWORK = os.path.join(ROOT, "work", "framework-oat")
LABEL = "u:object_r:system_file:s0"


def adb(*args):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True, errors="replace")


def sh(cmd):
    r = adb("shell", cmd)
    return (r.stdout or "") + (r.stderr or "")


def main():
    if "--confirm" not in sys.argv:
        print("refusing to write without --confirm")
        return 2
    if not sh("getprop ro.twrp.version").strip():
        print("device is not in TWRP; aborting")
        return 1
    sh("mount /system 2>&1; mount -o rw,remount /system 2>&1")

    pushed = failed = 0
    for dirpath, _, files in os.walk(TREE):
        odex = [f for f in files if f.endswith(".odex")]
        if not odex:
            continue
        rel = os.path.relpath(dirpath, TREE).replace("\\", "/")
        dest = "/system/" + rel
        sh(f"mkdir -p {dest}")
        r = adb("push", dirpath + "/.", dest + "/")
        if r.returncode != 0:
            failed += 1
            print("  FAIL", rel, (r.stderr or r.stdout).strip()[:120])
            continue
        pushed += len(odex)
        sh(f"chmod 644 {dest}/*.odex; chown 0:0 {dest}/*.odex; chcon {LABEL} {dest}/*.odex")

    fw = [f for f in sorted(os.listdir(FRAMEWORK)) if f.endswith(".odex")]
    if fw:
        sh("mkdir -p /system/framework/oat/arm")
        r = adb("push", FRAMEWORK + "/.", "/system/framework/oat/arm/")
        if r.returncode == 0:
            pushed += len(fw)
            sh(f"chmod 644 /system/framework/oat/arm/*.odex; chown 0:0 /system/framework/oat/arm/*.odex; "
               f"chcon {LABEL} /system/framework/oat/arm/*.odex")
        else:
            failed += 1
            print("  FAIL framework/oat", (r.stderr or r.stdout).strip()[:120])

    sh("sync")
    print(f"odex pushed: {pushed}   failed: {failed}")
    print("framework/oat/arm:", sh("ls /system/framework/oat/arm | wc -l").strip())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
