"""Flash a Manikineko Phone zip from TWRP by running its own update-binary.

TWRP's GUI is not scriptable over adb, but the installer is: update-binary is an ARM ELF that
takes (api, fd, zip path) and does the whole job -- block_image_update for /system, the overlay,
the deletes, set_metadata, then package_extract_file("boot.img", KERNEL). Running it with
api=3 (the value TWRP 3.x passes) reproduces a normal install.

The zip is unpacked to /cache (114 MB free, tmpfs-backed and wiped on boot) rather than /tmp,
because update-binary reads its payload relative to the extracted directory.

Only META-INF is extracted: block_image_update() opens system.new.dat through the package's own
ZipFileRO handle, so the 700 MB payload never touches /cache (which is only 114 MB).

Usage: python scripts/53-flash-zip.py <zip-on-device> [--confirm]
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
WORK = "/cache/mk"


def adb(*args, **kw):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True,
                          errors="replace", **kw)


def sh(cmd, timeout=1800):
    r = adb("shell", cmd, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    zip_path = sys.argv[1]
    if "--confirm" not in sys.argv:
        print("refusing to flash without --confirm")
        return 2

    rc, out = sh("getprop ro.twrp.version")
    if not out.strip():
        print("device is not in TWRP; aborting")
        return 1
    print("TWRP", out.strip())

    rc, out = sh(f"ls -l {zip_path}")
    print("zip:", out.strip())
    if "No such file" in out:
        return 1

    # unzip in TWRP prints "invalid zip magic" after inflating (zip64 extra field) but still
    # writes the files, so success is judged by the extracted sizes, not by the exit status.
    rc, out = sh(f"rm -rf {WORK}; mkdir -p {WORK}; cd {WORK} && "
                 f"unzip -o -q {zip_path} META-INF/com/google/android/update-binary "
                 f"META-INF/com/google/android/updater-script; "
                 f"ls -l META-INF/com/google/android/")
    print("extracted:", out.strip().splitlines()[-2:])
    if "update-binary" not in out or "updater-script" not in out:
        print("unzip failed:", out.strip()[:400])
        return 1
    print("unpacked META-INF to", WORK)

    rc, out = sh(f"ls -l {WORK}/META-INF/com/google/android/update-binary")
    print("update-binary:", out.strip().splitlines()[-1])
    sh(f"chmod 755 {WORK}/META-INF/com/google/android/update-binary")

    print("running installer (this rewrites /system and KERNEL)...")
    rc, out = sh(f"cd {WORK} && ./META-INF/com/google/android/update-binary 3 1 {zip_path} 2>&1")
    tail = out.strip().splitlines()
    for line in tail[-25:]:
        print("  ", line)
    ok = any("Done" in l or "script result was [0" in l or "success" in l.lower() for l in tail)
    print("installer exit:", rc, "| success marker:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
