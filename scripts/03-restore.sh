#!/bin/sh
# Phase 0 restore - DESTRUCTIVE. Writes partitions back from a backup dir.
# Requires typing the partition name to confirm each write.
# Usage: sh scripts/03-restore.sh backups/<stamp> [partition ...]
set -u

ROOT_DIR="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT_DIR/tools/platform-tools/adb.exe"

SRC="${1:-}"
[ -z "$SRC" ] && { echo "usage: sh scripts/03-restore.sh backups/<stamp> [partition ...]"; exit 1; }
shift || true
[ -d "$SRC" ] || { echo "no such backup dir: $SRC"; exit 1; }

BYNAME=$("$ADB" shell 'for d in /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name /dev/block/by-name; do [ -d "$d" ] && echo "$d" && break; done' 2>/dev/null | tr -d '\r')
[ -z "$BYNAME" ] && { echo "FATAL: by-name not found"; exit 1; }
echo "by-name dir: $BYNAME"

LIST="$*"
if [ -z "$LIST" ]; then
  LIST=$(ls "$SRC"/*.img.gz 2>/dev/null | sed 's#.*/##; s#\.img\.gz$##')
fi
[ -z "$LIST" ] && { echo "no .img.gz files in $SRC"; exit 1; }

echo
echo "About to restore into: $SRC"
echo "Partitions: $LIST"
echo
echo "WARNING: this overwrites the listed partitions. EFS/modem writes can"
echo "destroy the IMEI if the image is wrong. Have a second copy of the backup."
printf 'Type RESTORE to continue: '
read -r ans
[ "$ans" = "RESTORE" ] || { echo "aborted"; exit 1; }

for p in $LIST; do
  F="$SRC/$p.img.gz"
  [ -f "$F" ] || { echo "skip $p (no file)"; continue; }
  DEV="$BYNAME/$p"
  "$ADB" shell "[ -e $DEV ] && echo yes" 2>/dev/null | grep -q yes || { echo "skip $p (no device node)"; continue; }

  echo "---- restoring $p ----"
  gzip -dc "$F" | "$ADB" shell "su -c 'dd of=$DEV bs=1048576'" 2>&1 | tr -d '\r'
  HASH_DEV=$("$ADB" shell "su -c 'dd if=$DEV bs=1048576 2>/dev/null | md5sum 2>/dev/null || dd if=$DEV bs=1048576 2>/dev/null | md5'" 2>/dev/null | tr -d '\r' | awk '{print $1}')
  HASH_SRC=$(gzip -dc "$F" | md5sum | awk '{print $1}')
  if [ "$HASH_DEV" = "$HASH_SRC" ]; then
    echo "OK   $p verified"
  else
    echo "FAIL $p mismatch dev=$HASH_DEV src=$HASH_SRC"
  fi
done

echo
echo "Done. Reboot with: $ADB reboot"
