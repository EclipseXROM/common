#!/bin/sh
# Manikineko branding for LineageOS 13 (Android 6) on kanas. NOT the KitKat scripts (31/34): those would overwrite
# build.prop with the stock KitKat copy. This one edits the CURRENT device build.prop.
#   sh scripts/50-los-branding.sh apply | restore      (adb must be root: LineageOS userdebug is)
set -u
ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT/tools/platform-tools/adb.exe"
export MSYS_NO_PATHCONV=1
BK=/data/local/branding-backup-los
T=/data/local/tmp
A=/system/media/audio
D="$ROOT/branding/los"
sh_() { "$ADB" shell "$1" | tr -d '\r'; }
ctx() { sh_ "restorecon $* 2>/dev/null || chcon u:object_r:system_file:s0 $*"; }
"$ADB" devices | grep -q "device$" || { echo "FATAL: no device"; exit 1; }
[ "$(sh_ id | grep -c uid=0)" = "1" ] || { echo "FATAL: adb shell is not root"; exit 1; }

case "${1:-}" in
apply)
  # 1. backups (once)
  if ! sh_ "[ -f $BK/build.prop ] && echo yes" | grep -q yes; then
    sh_ "mkdir -p $BK; cp /system/build.prop /system/media/bootanimation.zip $BK/; cp /data/system/users/0/wallpaper_info.xml $BK/; cp -r $A/ringtones $A/notifications $A/alarms $BK/"
  fi
  for d in ringtones notifications alarms; do
    a=$(sh_ "ls $A/$d | grep -c .") ; b=$(sh_ "ls $BK/$d | grep -c .")
    [ "$a" -le "$b" ] || [ "$(sh_ "ls $A/$d | grep -c Manikineko")" != "0" ] || { echo "FATAL: backup of $d incomplete"; exit 1; }
  done
  "$ADB" pull $BK/build.prop "$D/build.prop.orig" >/dev/null || exit 1
  # 2. build.prop from the saved ORIGINAL (display id + default tones)
  python -I - <<PY || exit 1
import re
s = open(r"$D/build.prop.orig", newline="").read()
n, c = re.subn(r"(?m)^ro\.build\.display\.id=.*$", "ro.build.display.id=Manikineko 1.0", s); assert c == 1
for k, v in (("ringtone", "Manikineko_Ring.wav"), ("notification_sound", "Manikineko_Note.wav"), ("alarm_alert", "Manikineko_Alarm.wav")):
    n, c = re.subn(r"(?m)^ro\.config\.%s=.*$" % k, "ro.config.%s=%s" % (k, v), n); assert c == 1, k
open(r"$D/build.prop", "w", newline="").write(n)
PY
  cat > "$D/wallpaper_info.xml" <<XML
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<wp width="960" height="800" name="" />
XML
  "$ADB" push "$D/build.prop" $T/build.prop.new >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/boot/bootanimation.zip" $T/bootanimation.zip >/dev/null || exit 1
  "$ADB" push "$ROOT/branding/boot/wallpaper_960.jpg" $T/wallpaper.new >/dev/null || exit 1
  "$ADB" push "$D/wallpaper_info.xml" $T/wallpaper_info.new >/dev/null || exit 1
  for f in Manikineko_Ring Manikineko_Note Manikineko_Alarm; do "$ADB" push "$ROOT/branding/sounds/$f.wav" $T/$f.wav >/dev/null || exit 1; done
  # 3. /system
  sh_ "mount -o remount,rw /system"
  sh_ "cp $T/build.prop.new /system/build.prop; chmod 644 /system/build.prop; chown root:root /system/build.prop"
  sh_ "cp $T/bootanimation.zip /system/media/bootanimation.zip; chmod 644 /system/media/bootanimation.zip; chown root:root /system/media/bootanimation.zip"
  sh_ "rm -f $A/ringtones/* $A/notifications/* $A/alarms/*"
  sh_ "cp $T/Manikineko_Ring.wav $A/ringtones/; cp $T/Manikineko_Note.wav $A/notifications/; cp $T/Manikineko_Alarm.wav $A/alarms/; chmod 644 $A/ringtones/* $A/notifications/* $A/alarms/*; chown root:root $A/ringtones/* $A/notifications/* $A/alarms/*"
  ctx /system/build.prop /system/media/bootanimation.zip $A/ringtones/* $A/notifications/* $A/alarms/*
  sh_ "mount -o remount,ro /system"
  # 4. wallpaper
  sh_ "cp $T/wallpaper.new /data/system/users/0/wallpaper; cp $T/wallpaper_info.new /data/system/users/0/wallpaper_info.xml; chown system:system /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml; chmod 600 /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml"
  ctx /data/system/users/0/wallpaper /data/system/users/0/wallpaper_info.xml
  echo "== verify =="
  sh_ "grep -E 'display.id|ro.config.(ringtone|notification|alarm)' /system/build.prop; ls $A/ringtones $A/notifications $A/alarms; ls -l /system/media/bootanimation.zip"
  echo "applied. Reboot (SIM OUT!), then: sh scripts/50-los-branding.sh defaults"
  ;;
defaults)
  for pair in "ringtone ringtones/Manikineko_Ring.wav" "notification_sound notifications/Manikineko_Note.wav" "alarm_alert alarms/Manikineko_Alarm.wav"; do
    set -- $pair
    id=$("$ADB" shell "content query --uri content://media/internal/audio/media --projection _id --where \"_data='$A/$2'\"" | tr -d '\r' | grep -o '_id=[0-9]*' | head -1 | cut -d= -f2)
    [ -n "$id" ] || { echo "FATAL: $2 not in media DB yet"; exit 1; }
    "$ADB" shell settings put system $1 "content://media/internal/audio/media/$id"; echo "$1 -> $id"
  done
  ;;
restore)
  sh_ "mount -o remount,rw /system"
  sh_ "cp $BK/build.prop /system/build.prop; cp $BK/bootanimation.zip /system/media/bootanimation.zip; rm -f $A/ringtones/* $A/notifications/* $A/alarms/*; cp $BK/ringtones/* $A/ringtones/; cp $BK/notifications/* $A/notifications/; cp $BK/alarms/* $A/alarms/"
  sh_ "chmod 644 /system/build.prop /system/media/bootanimation.zip $A/ringtones/* $A/notifications/* $A/alarms/*; chown root:root /system/build.prop /system/media/bootanimation.zip $A/ringtones/* $A/notifications/* $A/alarms/*"
  ctx /system/build.prop /system/media/bootanimation.zip $A/ringtones/* $A/notifications/* $A/alarms/*
  sh_ "mount -o remount,ro /system; rm -f /data/system/users/0/wallpaper; cp $BK/wallpaper_info.xml /data/system/users/0/wallpaper_info.xml; chown system:system /data/system/users/0/wallpaper_info.xml; chmod 600 /data/system/users/0/wallpaper_info.xml"
  echo "restored. reboot and re-pick tones in Settings."
  ;;
*) echo "usage: sh scripts/50-los-branding.sh apply|defaults|restore"; exit 1 ;;
esac
