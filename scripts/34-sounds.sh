#!/bin/sh
# Replace Samsung ringtones/notifications/alarms with the Manikineko tones.
#   sh scripts/34-sounds.sh apply     (run scripts/31-branding.sh apply first: it sets ro.config defaults)
#   sh scripts/34-sounds.sh restore   (restores the original audio dirs from the device backup)
# /system/media/audio/ui (touch/lock sounds) is NOT touched.
set -u
ROOT="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT/tools/platform-tools/adb.exe"
export MSYS_NO_PATHCONV=1
BK=/data/local/branding-backup/audio
A=/system/media/audio
T=/data/local/tmp
sh_() { "$ADB" shell "su -c \"$1\"" | tr -d '\r'; }
"$ADB" devices | grep -q "device$" || { echo "FATAL: no device"; exit 1; }

case "${1:-}" in
apply)
  for f in Manikineko_Ring Manikineko_Note Manikineko_Alarm; do
    "$ADB" push "$ROOT/branding/sounds/$f.wav" $T/$f.wav >/dev/null || exit 1
  done
  if ! sh_ "ls $BK/ringtones >/dev/null 2>&1 && echo yes" | grep -q yes; then
    sh_ "mkdir -p $BK; cp -r $A/ringtones $A/notifications $A/alarms $BK/"
  fi
  # refuse to delete anything unless the backup is complete
  for d in ringtones notifications alarms; do
    a=$(sh_ "ls $A/$d | grep -c .") ; b=$(sh_ "ls $BK/$d | grep -c .")
    [ "$a" -le "$b" ] || { echo "FATAL: backup of $d incomplete ($b < $a)"; exit 1; }
  done
  sh_ "mount -o remount,rw /system"
  sh_ "rm -f $A/ringtones/* $A/notifications/* $A/alarms/*"
  sh_ "cp $T/Manikineko_Ring.wav $A/ringtones/; cp $T/Manikineko_Note.wav $A/notifications/; cp $T/Manikineko_Alarm.wav $A/alarms/"
  sh_ "chmod 644 $A/ringtones/* $A/notifications/* $A/alarms/*; chown root:root $A/ringtones/* $A/notifications/* $A/alarms/*; chcon u:object_r:system_file:s0 $A/ringtones/* $A/notifications/* $A/alarms/*"
  sh_ "mount -o remount,ro /system"
  sh_ "ls -lZ $A/ringtones $A/notifications $A/alarms"
  echo "applied. reboot (media scan), then run: sh scripts/34-sounds.sh defaults"
  ;;
defaults)
  # after the reboot scan: point the current settings at the new media ids
  for pair in "ringtone ringtones/Manikineko_Ring.wav" "notification_sound notifications/Manikineko_Note.wav" "alarm_alert alarms/Manikineko_Alarm.wav"; do
    set -- $pair
    id=$("$ADB" shell "content query --uri content://media/internal/audio/media --projection _id --where \"_data='$A/$2'\"" | tr -d '\r' | grep -o '_id=[0-9]*' | head -1 | cut -d= -f2)
    [ -n "$id" ] || { echo "FATAL: $2 not in media DB yet (reboot done?)"; exit 1; }
    "$ADB" shell settings put system $1 "content://media/internal/audio/media/$id"
    echo "$1 -> $id"
  done
  ;;
restore)
  sh_ "mount -o remount,rw /system"
  sh_ "rm -f $A/ringtones/* $A/notifications/* $A/alarms/*; cp $BK/ringtones/* $A/ringtones/; cp $BK/notifications/* $A/notifications/; cp $BK/alarms/* $A/alarms/"
  sh_ "chmod 644 $A/ringtones/* $A/notifications/* $A/alarms/*; chown root:root $A/ringtones/* $A/notifications/* $A/alarms/*; chcon u:object_r:system_file:s0 $A/ringtones/* $A/notifications/* $A/alarms/*"
  sh_ "mount -o remount,ro /system"
  echo "restored audio files. Also run scripts/31-branding.sh restore (ro.config defaults), reboot, and re-pick tones in Settings."
  ;;
*) echo "usage: sh scripts/34-sounds.sh apply|defaults|restore"; exit 1 ;;
esac
