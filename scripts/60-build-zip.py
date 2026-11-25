"""Build the Manikineko Phone TWRP-flashable zip (SM-G355HN / kanas3gnfc).

Contents
  * LineageOS 13.0 base: update-binary + block-based system image from the SandroidTeam zip (untouched)
  * boot.img                 = recon/boot/boot-hybrid.img (stock 3.10.17 kernel + patched LOS ramdisk, scripts/42-hybrid-boot.py)
  * manikineko/system/...    = overlay applied on top of the system image (branding, Wi-Fi fw, libion_sprd, launcher, build.prop,
                               first-boot provisioning script)
Only reads the project; writes build/manikineko-phone-1.8-kanas3gnfc.zip
"""
import hashlib, os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)
BASE = J("twrp", "lineage-13.0-20170317-UNOFFICIAL-kanas-SandroidTeam-Ih24n.zip")
OUT = J("build", "manikineko-phone-1.8-kanas3gnfc.zip")
VERSION = "1.8"

# Packages removed from /system/app by scripts/52-debloat-system.py. The overlay cannot delete
# anything, so the installer has to: without this a fresh flash brings all 23 back.
DEBLOAT = [
    "Email", "Exchange2", "HexoLibre", "Eleven", "CMWallpapers", "Browser", "Terminal",
    "PrintSpooler", "SoundRecorder", "PhotoPhase", "PhotoTable", "BasicDreams", "Galaxy4",
    "NoiseField", "PhaseBeam", "HoloSpiralWallpaper", "LiveWallpapers", "SandroidTeamStats",
    "HTMLViewer", "Stk", "WAPPushManager", "Calendar", "LockClock",
]

FIRSTBOOT = """#!/system/bin/sh
# Manikineko Phone first-boot provisioning: runs once per fresh /data, then reboots once.
M=/data/misc/manikineko_firstboot_done
[ -f $M ] && exit 0
/system/bin/setsid /system/bin/sh -c '
  M=/data/misc/manikineko_firstboot_done
  i=0
  while [ "$(getprop sys.boot_completed)" != 1 ] && [ $i -lt 150 ]; do sleep 2; i=$((i+1)); done
  sleep 8
  settings put global device_provisioned 1
  settings put secure user_setup_complete 1
  settings --cm put secure cm_setup_wizard_completed 1
  mkdir -p /data/system/users/0
  if [ ! -f /data/system/users/0/wallpaper ]; then
    cp /system/etc/manikineko/wallpaper /data/system/users/0/wallpaper
    cp /system/etc/manikineko/wallpaper_info.xml /data/system/users/0/wallpaper_info.xml
    chown system:system /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml
    chmod 600 /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml
  fi
  touch $M
  sleep 3
  reboot
' >/dev/null 2>&1 &
exit 0
"""

WALLPAPER_INFO = "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<wp width=\"960\" height=\"800\" name=\"\" />\n"

# (archive path under manikineko/system, source file or bytes, octal mode)
OVERLAY = [
    ("build.prop", J("branding", "los", "build.prop.singlesim"), 0o644),
    ("media/bootanimation.zip", J("branding", "boot", "bootanimation.zip"), 0o644),
    ("media/audio/ringtones/Manikineko_Ring.wav", J("branding", "sounds", "Manikineko_Ring.wav"), 0o644),
    ("media/audio/notifications/Manikineko_Note.wav", J("branding", "sounds", "Manikineko_Note.wav"), 0o644),
    ("media/audio/alarms/Manikineko_Alarm.wav", J("branding", "sounds", "Manikineko_Alarm.wav"), 0o644),
    ("etc/wifi/bcmdhd.cal", J("recon", "wifi", "stock", "nvram_net.txt"), 0o644),
    ("etc/firmware/fw_bcmdhd.bin", J("recon", "wifi", "stock", "bcmdhd_sta.bin"), 0o644),
    ("etc/firmware/fw_bcmdhd_apsta.bin", J("recon", "wifi", "stock", "bcmdhd_apsta.bin"), 0o644),
    ("lib/libion_sprd.so", J("recon", "camera", "libion.so"), 0o644),
    ("app/ManikinekoHome/ManikinekoHome.apk", J("build", "manikineko-home.apk"), 0o644),
    ("app/ManikinekoNotes/ManikinekoNotes.apk", J("build", "ManikinekoNotes.apk"), 0o644),
    ("app/ManikinekoFiles/ManikinekoFiles.apk", J("build", "ManikinekoFiles.apk"), 0o644),
    ("app/ManikinekoBrowser/ManikinekoBrowser.apk", J("build", "ManikinekoBrowser.apk"), 0o644),
    ("app/ManikinekoStore/ManikinekoStore.apk", J("build", "ManikinekoStore.apk"), 0o644),
    ("etc/manikineko/wallpaper", J("branding", "boot", "wallpaper_960.jpg"), 0o644),
    ("etc/manikineko/wallpaper_info.xml", WALLPAPER_INFO.encode(), 0o644),
    ("etc/init.d/50manikineko-firstboot", FIRSTBOOT.encode(), 0o755),
    # Android 6 has no ISRG Root X1 (Let's Encrypt, added in 7.1.1); f-droid.org's chain (YR1 -> Root YR -> X1) needs it.
    # Official cert from letsencrypt.org, sha256 96:BC:EC:06:...:08:C6 verified; file name = openssl subject_hash_old
    ("etc/security/cacerts/6187b673.0", J("recon", "fdroid", "6187b673.0"), 0o644),
    # mac_permissions.xml maps our signer certificate to seinfo "platform"; without it every
    # re-signed package dies in selinux_android_setcontext (scripts/51-mac-permissions.py).
    ("etc/security/mac_permissions.xml", J("work", "mac_permissions.xml"), 0o644),
]

# The 62 packages re-signed by scripts/46-resign-system.py. The base system image still carries the
# original SandroidTeam signatures, so without these the flash reverts About phone to Ih24n and the
# shared-uid members get dropped. Paths mirror /system exactly.
RESIGNED = J("work", "resigned")
TREE = J("work", "oat-tree")
FRAMEWORK = J("work", "framework-oat")

ASSERT_DEVICES = ["kanas", "kanas3g", "kanas3gxx", "kanas3gub", "kanas3gnfcxx", "kanas3gnfc", "SM-G355H", "SM-G355HN", "SM-G355M"]
BLK = "/dev/block/platform/sprd-sdhci.3/by-name"
SYSDEV, KERNELDEV = f"{BLK}/system", f"{BLK}/KERNEL"
LABEL = '"selabel", "u:object_r:system_file:s0", "capabilities", 0x0'


def _debloated(rel):
    """True for overlay paths under a /system/app dir that DEBLOAT removes.

    Five packages are both re-signed and debloated (Eleven, Browser, SoundRecorder, PhotoPhase,
    Stk). The installer deletes them first, so the overlay must not put them back.
    """
    parts = rel.split("/")
    return len(parts) > 2 and parts[0] == "app" and parts[1] in DEBLOAT


def resigned_overlay():
    """(archive path under manikineko/system, source file, mode) for every re-signed APK."""
    out = []
    for dirpath, _, files in os.walk(RESIGNED):
        for f in sorted(files):
            if not f.endswith(".apk"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, RESIGNED).replace("\\", "/")
            if _debloated(rel):
                continue
            out.append((rel, full, 0o644))
    out.sort()
    return out


def oat_overlay():
    """(archive path under manikineko/system, source file, mode) for the odex trees.

    The ROM ships stripped APKs, so ART loads them only through the matching .odex. The
    installer deletes every oat directory of a re-signed package (stale odex were compiled
    against the old certificates) and this overlay puts the trees back. Without it the boot
    classpath dies with "No original dex files found for dex location ...".
    """
    out = []
    for dirpath, _, files in os.walk(TREE):
        for f in sorted(files):
            if not f.endswith(".odex"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, TREE).replace("\\", "/")
            if _debloated(rel):
                continue
            out.append((rel, full, 0o644))
    for f in sorted(os.listdir(FRAMEWORK)):
        if f.endswith(".odex") and not os.path.exists(os.path.join(TREE, "framework", "oat", "arm", f)):
            out.append(("framework/oat/arm/" + f, os.path.join(FRAMEWORK, f), 0o644))
    out.sort()
    return out


def updater_script():
    cond = " || ".join(f'getprop("ro.product.device") == "{d}" || getprop("ro.build.product") == "{d}"' for d in ASSERT_DEVICES)
    abort = f'abort("This package is for device: {",".join(ASSERT_DEVICES)}; this device is " + getprop("ro.product.device") + ".")'
    meta = lambda path, extra="": f'set_metadata_recursive("{path}", "uid", 0, "gid", 0, "dmode", 0755, "fmode", 0644, {LABEL});'
    lines = [
        f"assert({cond} || {abort};);",
        f'ui_print("Manikineko Phone {VERSION}");',
        'ui_print("LineageOS 13.0 base + stock 3.10.17 kernel (hybrid), SM-G355HN");',
        'ui_print("Tip: wipe data/cache/dalvik first for a clean first boot.");',
        'ifelse(is_mounted("/system"), unmount("/system"));',
        'show_progress(0.600000, 0);',
        'ui_print("Writing system image...");',
        f'block_image_update("{SYSDEV}", package_extract_file("system.transfer.list"), "system.new.dat", "system.patch.dat") || abort("System image update failed.");',
        'show_progress(0.150000, 5);',
        'ui_print("Applying Manikineko overlay...");',
        f'mount("ext4", "EMMC", "{SYSDEV}", "/system", "");',
        # remove what the overlay replaces / does not want
        'delete_recursive("/system/priv-app/Trebuchet", "/system/priv-app/CyanogenSetupWizard");',
        'delete_recursive("/system/media/audio/ringtones", "/system/media/audio/notifications", "/system/media/audio/alarms");',
        'ui_print("Removing unused system apps...");',
        "delete_recursive(" + ", ".join(f'"/system/app/{d}"' for d in DEBLOAT) + ");",
        # stale oat was compiled against the old certificates; ART must recompile
        "delete_recursive(" + ", ".join(f'"/system/{os.path.dirname(rel)}/oat"' for rel, _, _ in resigned_overlay()) + ");",
        'package_extract_dir("manikineko/system", "/system");',
        meta("/system/media/audio"),
        meta("/system/etc/wifi"), meta("/system/etc/firmware"), meta("/system/etc/manikineko"),
        meta("/system/app/ManikinekoHome"),
        meta("/system/app/ManikinekoNotes"),
        meta("/system/app/ManikinekoFiles"),
        meta("/system/app/ManikinekoBrowser"),
        meta("/system/app/ManikinekoStore"),
        *[meta("/system/" + os.path.dirname(rel)) for rel, _, _ in resigned_overlay()],
        f'set_metadata("/system/build.prop", "uid", 0, "gid", 0, "mode", 0644, {LABEL});',
        f'set_metadata("/system/media/bootanimation.zip", "uid", 0, "gid", 0, "mode", 0644, {LABEL});',
        f'set_metadata("/system/lib/libion_sprd.so", "uid", 0, "gid", 0, "mode", 0644, {LABEL});',
        f'set_metadata("/system/etc/init.d/50manikineko-firstboot", "uid", 0, "gid", 0, "mode", 0755, {LABEL});',
        f'set_metadata("/system/etc/security/cacerts/6187b673.0", "uid", 0, "gid", 0, "mode", 0644, {LABEL});',
        'unmount("/system");',
        'show_progress(0.150000, 5);',
        'ui_print("Writing boot image (KERNEL)...");',
        f'package_extract_file("boot.img", "{KERNELDEV}");',
        'show_progress(0.100000, 0);',
        'ui_print("Done. First boot reboots once by itself to finish setup.");',
    ]
    return "\n".join(lines) + "\n"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    base = zipfile.ZipFile(BASE)
    # sanity: our build.prop must only differ from the base build.prop by the intended keys
    bp_base = dict(l.split("=", 1) for l in base.read("system/build.prop").decode().splitlines() if "=" in l and not l.startswith("#"))
    bp_ours = dict(l.split("=", 1) for l in open(J("branding", "los", "build.prop.singlesim"), encoding="utf-8").read().splitlines() if "=" in l and not l.startswith("#"))
    changed = sorted(k for k in set(bp_base) | set(bp_ours) if bp_base.get(k) != bp_ours.get(k))
    expected = {"ro.build.display.id", "ro.config.ringtone", "ro.config.notification_sound", "ro.config.alarm_alert",
                "ro.modem.w.count", "ro.msms.phone_count", "persist.msms.phone_count", "persist.radio.multisim.config",
                "ro.build.date", "ro.build.date.utc", "ro.build.user", "ro.build.host",
                "ro.build.description", "ro.build.fingerprint", "ro.product.name",
                "ro.cm.version", "ro.modversion", "ro.cm.display.version",
                "ro.romstats.url", "ro.romstats.name", "ro.romstats.version",
                "ro.romstats.tframe", "ro.romstats.askfirst", "ro.romstats.ga"}
    print("build.prop keys changed vs LOS base:", changed)
    assert set(changed) == expected, "unexpected build.prop drift: %s" % (set(changed) ^ expected)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    manifest = []
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        def add_bytes(arc, data, mode=0o644):
            zi = zipfile.ZipInfo(arc, (2026, 11, 24, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = (0o100000 | mode) << 16
            z.writestr(zi, data); manifest.append((arc, len(data), sha(data)))
        # base (copied byte for byte through read/write; system image streamed)
        add_bytes("META-INF/com/google/android/update-binary", base.read("META-INF/com/google/android/update-binary"), 0o755)
        add_bytes("META-INF/com/google/android/updater-script", updater_script().encode())
        for name in ("system.transfer.list", "system.patch.dat", "file_contexts"):
            add_bytes(name, base.read(name))
        zi = zipfile.ZipInfo("system.new.dat", (2026, 11, 24, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
        h = hashlib.sha256(); n = 0
        with base.open("system.new.dat") as src, z.open(zi, "w", force_zip64=True) as dst:
            while True:
                b = src.read(1 << 22)
                if not b: break
                dst.write(b); h.update(b); n += len(b)
        manifest.append(("system.new.dat", n, h.hexdigest()))
        add_bytes("boot.img", open(J("recon", "boot", "boot-hybrid.img"), "rb").read())
        for arc, src, mode in OVERLAY + resigned_overlay() + oat_overlay():
            data = open(src, "rb").read() if isinstance(src, str) else src
            add_bytes("manikineko/system/" + arc, data, mode)
        add_bytes("MANIFEST.txt", ("Manikineko Phone %s - SM-G355HN\n" % VERSION + "".join(f"{s}  {n:>10}  {a}\n" for a, n, s in manifest)).encode())
    print("written", OUT, os.path.getsize(OUT), "bytes")
    print("zip sha256", hashlib.sha256(open(OUT, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
