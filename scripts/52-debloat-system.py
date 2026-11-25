"""Remove unused AOSP/CyanogenMod packages from /system/app to reclaim space.

The launcher only shows the nine packages in launcher/res/values/arrays.xml, so everything
else in /system/app is dead weight on a 1 GB /system partition. The list below is limited to
packages with no system dependency: no whitelisted launcher entry, no HAL, no provider that
another package queries, and nothing Settings launches by class name.

Deliberately kept: CMFileManager (useful utility), PicoTts (TTS engine, 96 KB), ThemeChooser
and AudioFX (Settings opens both by class name, removing them would crash those screens),
CMUpdater (the "LineageOS updates" row in About phone launches it).

Run only from TWRP. PackageManagerService drops the packages.xml entries for packages whose
APK is gone, so no XML surgery is needed.

Usage: python scripts/52-debloat-system.py [--dry-run | --confirm]
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")

# dir under /system/app -> package name, for the report
REMOVE = [
    ("Email", "com.android.email"),
    ("Exchange2", "com.android.exchange"),
    ("HexoLibre", "org.cyanogenmod.hexolibre"),
    ("Eleven", "com.cyanogenmod.eleven"),
    ("CMWallpapers", "com.cyanogenmod.wallpapers"),
    ("Browser", "com.android.browser"),
    ("Terminal", "com.android.terminal"),
    ("PrintSpooler", "com.android.printspooler"),
    ("SoundRecorder", "com.android.soundrecorder"),
    ("PhotoPhase", "org.cyanogenmod.wallpapers.photophase"),
    ("PhotoTable", "com.android.dreams.phototable"),
    ("BasicDreams", "com.android.dreams.basic"),
    ("Galaxy4", "com.android.galaxy4"),
    ("NoiseField", "com.android.noisefield"),
    ("PhaseBeam", "com.android.phasebeam"),
    ("HoloSpiralWallpaper", "com.android.wallpaper.holospiral"),
    ("LiveWallpapers", "com.android.wallpaper"),
    ("SandroidTeamStats", "android.romstats"),
    ("HTMLViewer", "com.android.htmlviewer"),
    ("Stk", "com.android.stk"),
    ("WAPPushManager", "com.android.smspush"),
    ("Calendar", "com.android.calendar"),
    ("LockClock", "com.cyanogenmod.lockclock"),
]


def adb(*args):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True, errors="replace")


def sh(cmd):
    r = adb("shell", cmd)
    return (r.stdout or "") + (r.stderr or "")


def df_data():
    out = sh("df /system | tail -1")
    parts = out.split()
    return int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else -1


def main():
    dry = "--dry-run" in sys.argv
    confirm = "--confirm" in sys.argv
    if not dry and not confirm:
        print("refusing to delete without --confirm (or use --dry-run)")
        return 2

    if not dry:
        if not sh("getprop ro.twrp.version").strip():
            print("device is not in TWRP; aborting")
            return 1
        print("TWRP", sh("getprop ro.twrp.version").strip())
        sh("mount /system 2>&1; mount -o rw,remount /system 2>&1")

    present, missing, total = [], [], 0
    for d, pkg in REMOVE:
        size = sh(f"du -sk /system/app/{d} 2>/dev/null | cut -f1").strip()
        if size.isdigit():
            present.append((d, pkg, int(size)))
            total += int(size)
        else:
            missing.append((d, pkg))

    print(f"to remove: {len(present)} dirs, {total} KB ({total / 1024:.1f} MB)")
    for d, pkg, size in present:
        print(f"  {size:6} KB  {d:22} {pkg}")
    if missing:
        print(f"already absent: {len(missing)}")
        for d, pkg in missing:
            print(f"          {d:22} {pkg}")

    if dry:
        return 0

    before = df_data()
    failed = []
    for d, pkg, size in present:
        out = sh(f"rm -rf /system/app/{d}; test -d /system/app/{d} && echo STILL_THERE || echo gone")
        if "gone" not in out:
            failed.append((d, out.strip()[:120]))
    sh("sync")
    after = df_data()

    print(f"removed: {len(present) - len(failed)}   failed: {len(failed)}")
    for d, why in failed:
        print("  FAIL", d, why)
    if before > 0 and after > 0:
        print(f"/system free: {before} KB -> {after} KB (+{after - before} KB)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
