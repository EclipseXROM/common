"""Re-sign the /system packages that must share one certificate with Settings.apk.

Settings.apk cannot be re-signed on its own: it belongs to the android.uid.system shared
user, and it holds signature-level permissions defined by framework-res.apk. Changing its
certificate therefore forces the same certificate onto

  * every member of android.uid.system (shared-user signature must match), and
  * every package holding a signature permission defined by framework-res.apk or
    org.cyanogenmod.platform-res.apk (the definer's certificate changes too).

The set is computed from work/signature-dependents.json plus the shared-uid membership
below, never hand-listed. Input APKs come from backup/system-apks (pulled from the device),
output goes to work/resigned/<same relative path>.

Usage: python scripts/46-resign-system.py [--dry-run]
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BT = os.path.join(ROOT, "tools", "sdk", "build-tools", "30.0.3")
JAVA_HOME = os.path.join(ROOT, "tools", "jdk-17.0.21.1+2")
KS = os.environ.get("MK_KS", os.path.join(os.environ.get("MK_BUILD", "C:/mkbuild"), "manikineko.keystore"))
KS_PASS = "manikineko"
KS_ALIAS = "manikineko"

SRC = os.path.join(ROOT, "backup", "system-apks")
OUT = os.path.join(ROOT, "work", "resigned")
DEPS = os.path.join(ROOT, "work", "signature-dependents.json")

# android.uid.system members, from `dumpsys package` on the device (userId=1000).
SHARED_UID_SYSTEM = [
    "app/DownloadProviderUi/DownloadProviderUi.apk",
    "app/Development/Development.apk",
    "app/KeyChain/KeyChain.apk",
    "app/UserDictionaryProvider/UserDictionaryProvider.apk",
    "framework/framework-res.apk",
    "framework/org.cyanogenmod.platform-res.apk",
    "priv-app/AudioFX/AudioFX.apk",
    "priv-app/BackupRestoreConfirmation/BackupRestoreConfirmation.apk",
    "priv-app/CMAudioService/CMAudioService.apk",
    "priv-app/CMSettingsProvider/CMSettingsProvider.apk",
    "priv-app/CMUpdater/CMUpdater.apk",
    "priv-app/CalendarProvider/CalendarProvider.apk",
    "priv-app/CallLogBackup/CallLogBackup.apk",
    "priv-app/CarrierConfig/CarrierConfig.apk",
    "priv-app/CellBroadcastReceiver/CellBroadcastReceiver.apk",
    "priv-app/Contacts/Contacts.apk",
    "priv-app/ContactsProvider/ContactsProvider.apk",
    "priv-app/DataUsageProvider/DataUsageProvider.apk",
    "priv-app/DefaultContainerService/DefaultContainerService.apk",
    "priv-app/DownloadProvider/DownloadProvider.apk",
    "priv-app/FMRadio/FMRadio.apk",
    "priv-app/FusedLocation/FusedLocation.apk",
    "priv-app/InputDevices/InputDevices.apk",
    "priv-app/MediaProvider/MediaProvider.apk",
    "priv-app/Settings/Settings.apk",
    "priv-app/SettingsProvider/SettingsProvider.apk",
    "priv-app/Telecom/Telecom.apk",
]

# android.uid.phone members (userId=1001). SamsungServiceMode is not a signature-permission
# holder, so it only shows up here: without it PMS drops the package with
# "Signature mismatch for shared user : android.uid.phone/1001".
SHARED_UID_PHONE = [
    "app/SamsungServiceMode/SamsungServiceMode.apk",
    "priv-app/MmsService/MmsService.apk",
    "priv-app/TeleService/TeleService.apk",
    "priv-app/TelephonyProvider/TelephonyProvider.apk",
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace", **kw)


# About-phone rows live as literal strings in res/xml/device_info_settings.xml. The file is
# binary XML, so the strings are replaced in place with equal-length text: the string pool
# length prefixes and every chunk offset stay valid, and trailing spaces are invisible.
SETTINGS_ROWS = [
    (b"Muhammad Ihsan a.k.a Ih24n", b"Manikineko"),
    (b"My(Ih24n) Sweetheart", b"Manikineko Phone"),
    (b"Intan Fatmawati", b"manikineko.nl"),
    (b"SandroidTeam", b"ZygHosting"),
]
SETTINGS_XML = "res/xml/device_info_settings.xml"


def patch_settings(src, dst):
    """Rewrite the About-phone rows into dst; returns a list of applied replacements."""
    import zipfile

    applied = []
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == SETTINGS_XML:
                for old, new in SETTINGS_ROWS:
                    if data.count(old) != 1:
                        raise SystemExit(f"{old!r} appears {data.count(old)}x in {SETTINGS_XML}")
                    data = data.replace(old, new + b" " * (len(old) - len(new)))
                    applied.append((old.decode(), new.decode()))
            zout.writestr(info, data)
    return applied


def main():
    dry = "--dry-run" in sys.argv
    env = dict(os.environ, JAVA_HOME=JAVA_HOME)
    env["PATH"] = os.path.join(JAVA_HOME, "bin") + os.pathsep + env.get("PATH", "")

    deps = json.load(open(DEPS, encoding="utf-8"))
    holders = {p["apk"] for p in deps["packages"] if p["count"]}
    targets = sorted(holders | set(SHARED_UID_SYSTEM) | set(SHARED_UID_PHONE))
    print(f"signature-permission holders: {len(holders)}")
    print(f"android.uid.system members:   {len(SHARED_UID_SYSTEM)}")
    print(f"android.uid.phone members:    {len(SHARED_UID_PHONE)}")
    print(f"union to re-sign:             {len(targets)}")

    if dry:
        for t in targets:
            print("  ", t)
        return 0

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    ok, failed = [], []
    for rel in targets:
        src = os.path.join(SRC, rel.replace("/", os.sep))
        dst = os.path.join(OUT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if rel == "priv-app/Settings/Settings.apk":
            staged = dst + ".patched"
            for old, new in patch_settings(src, staged):
                print(f"  Settings row: {old!r} -> {new!r}")
            src = staged
        aligned = dst + ".aligned"
        r = run([os.path.join(BT, "zipalign.exe"), "-f", "-p", "4", src, aligned], env=env)
        if r.returncode != 0:
            failed.append((rel, "zipalign: " + (r.stderr or r.stdout).strip()[:200]))
            continue
        r = run([os.path.join(BT, "apksigner.bat"), "sign",
                 "--ks", KS, "--ks-pass", "pass:" + KS_PASS,
                 "--key-pass", "pass:" + KS_PASS, "--ks-key-alias", KS_ALIAS,
                 "--min-sdk-version", "23", "--out", dst, aligned], env=env)
        os.remove(aligned)
        if src.endswith(".patched"):
            os.remove(src)
        if r.returncode != 0:
            failed.append((rel, "sign: " + (r.stderr or r.stdout).strip()[:200]))
            continue
        r = run([os.path.join(BT, "apksigner.bat"), "verify",
                 "--min-sdk-version", "23", dst], env=env)
        if r.returncode != 0:
            failed.append((rel, "verify: " + (r.stderr or r.stdout).strip()[:200]))
            continue
        ok.append(rel)

    print(f"signed+verified: {len(ok)}   failed: {len(failed)}")
    for rel, why in failed:
        print("  FAIL", rel, why)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
