#!/bin/sh
# Phase 3 branding: bootanimation, build display id, default wallpaper.
#   sh scripts/31-branding.sh apply     (backs up first, device /data/local/branding-backup)
#   sh scripts/31-branding.sh restore   (puts originals back, removes wallpaper override)
# Touches ONLY: /system/media/bootanimation.zip, /system/build.prop (display.id line),
# /system/wallpaper/ (lockscreen default, did not exist before), /data/system/users/0/wallpaper(+_info.xml). No bootloader/modem/EFS.
set -u
ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT/tools/platform-tools/adb.exe"
export MSYS_NO_PATHCONV=1
BK=/data/local/branding-backup
T=/data/local/tmp
sh_() { "$ADB" shell "su -c \"$1\"" | tr -d '\r'; }

"$ADB" devices | grep -q "device$" || { echo "FATAL: no device"; exit 1; }

case "${1:-}" in
apply)
  # build.prop: only the display.id line changes (host-side, device toolbox has no sed)
  python -I - <<PY || exit 1
import re
s = open(r"$ROOT/branding/orig/build.prop", newline="").read()
n = re.sub(r"(?m)^ro\.build\.display\.id=.*$", "ro.build.display.id=Manikineko 1.0", s)
assert n != s, "display.id line not found"
for k, v in (("ringtone", "Manikineko_Ring.wav"), ("notification_sound", "Manikineko_Note.wav"), ("alarm_alert", "Manikineko_Alarm.wav")):
    n, c = re.subn(r"(?m)^ro\.config\.%s=.*$" % k, "ro.config.%s=%s" % (k, v), n)
    assert c == 1, k
open(r"$ROOT/branding/boot/build.prop", "w", newline="").write(n)
PY
  cat > "$ROOT/branding/boot/wallpaper_info.xml" <<XML
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<wp width="800" height="800" name="" />
XML
  "$ADB" push "$ROOT/branding/boot/bootanimation.zip" $T/bootanimation.zip >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/boot/build.prop" $T/build.prop.new >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/boot/wallpaper_800.jpg" $T/wallpaper.new >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/boot/wallpaper_info.xml" $T/wallpaper_info.new >/dev/null || exit 1
  sh_ "mkdir -p $BK; [ -f $BK/wallpaper_info.xml ] || cp /data/system/users/0/wallpaper_info.xml $BK/wallpaper_info.xml; ls $BK"
  sh_ "mount -o remount,rw /system"
  sh_ "cp $T/bootanimation.zip /system/media/bootanimation.zip; chmod 644 /system/media/bootanimation.zip; chown root:root /system/media/bootanimation.zip; chcon u:object_r:system_file:s0 /system/media/bootanimation.zip"
  sh_ "cp $T/build.prop.new /system/build.prop; chmod 644 /system/build.prop; chown root:root /system/build.prop; chcon u:object_r:system_file:s0 /system/build.prop"
  "$ADB" push "$ROOT/branding/wallpapers/frame_6_480x800.jpg" $T/lockdef.jpg >/dev/null || exit 1
  sh_ "mkdir -p /system/wallpaper; cp $T/lockdef.jpg /system/wallpaper/lockscreen_default_wallpaper.jpg; chmod 755 /system/wallpaper; chmod 644 /system/wallpaper/lockscreen_default_wallpaper.jpg; chown root:root /system/wallpaper /system/wallpaper/lockscreen_default_wallpaper.jpg; chcon u:object_r:system_file:s0 /system/wallpaper /system/wallpaper/lockscreen_default_wallpaper.jpg"
  sh_ "mount -o remount,ro /system"
  sh_ "cp $T/wallpaper.new /data/system/users/0/wallpaper; cp $T/wallpaper_info.new /data/system/users/0/wallpaper_info.xml; chown system:system /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml; chmod 600 /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml; chcon u:object_r:system_data_file:s0 /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml"
  echo "== verify =="
  sh_ "ls -lZ /system/media/bootanimation.zip /system/build.prop /data/system/users/0/wallpaper*; grep display.id /system/build.prop"
  echo "applied. reboot to see it: adb reboot"
  ;;
restore)
  "$ADB" push "$ROOT/branding/orig/bootanimation.zip" $T/bootanimation.zip >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/orig/build.prop" $T/build.prop.new >/dev/null || exit 1
  sh_ "mount -o remount,rw /system"
  sh_ "cp $T/bootanimation.zip /system/media/bootanimation.zip; cp $T/build.prop.new /system/build.prop; chmod 644 /system/media/bootanimation.zip /system/build.prop; chown root:root /system/media/bootanimation.zip /system/build.prop; chcon u:object_r:system_file:s0 /system/media/bootanimation.zip /system/build.prop"
  sh_ "rm -rf /system/wallpaper"
  sh_ "mount -o remount,ro /system"
  sh_ "rm -f /data/system/users/0/wallpaper; cp $BK/wallpaper_info.xml /data/system/users/0/wallpaper_info.xml; chown system:system /data/system/users/0/wallpaper_info.xml; chmod 600 /data/system/users/0/wallpaper_info.xml; chcon u:object_r:system_data_file:s0 /data/system/users/0/wallpaper_info.xml"
  echo "restored. reboot."
  ;;
*) echo "usage: sh scripts/31-branding.sh apply|restore"; exit 1 ;;
esac
