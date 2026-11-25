#!/bin/sh
# Phase 0 backup - READ ONLY on the device (dd reads partitions, writes nothing).
# Streams each partition to the PC, gzip-compressed, and verifies md5 both sides.
# Usage: sh scripts/02-backup.sh
set -u

ROOT_DIR="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT_DIR/tools/platform-tools/adb.exe"
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$ROOT_DIR/backups/$STAMP"

# Partitions we want, using the REAL by-name entries of SM-G355HN (kanas3gnfc).
# There is no "boot"/"recovery"/"modem" name here: KERNEL, RECOVERY, MODEM.
# Missing ones are skipped, not fatal.
PARTS="KERNEL RECOVERY system userdata CSC efs MODEM MODEM_BACKUP FIXNV1 FIXNV2 RUNTIMENV1 RUNTIMENV2 prodnv PARAM HIDDEN OTA FOTA_SIG SBL1 SBL2 WDSP WDSP_BACKUP Odin_reserved"

mkdir -p "$OUT" || exit 1
LOG="$OUT/backup.log"
: > "$LOG"

log() { printf '%s\n' "$*" | tee -a "$LOG"; }

log "backup started $STAMP"
log "output dir: $OUT"

# --- locate by-name dir ---
BYNAME=$("$ADB" shell 'for d in /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name /dev/block/by-name; do [ -d "$d" ] && echo "$d" && break; done' 2>/dev/null | tr -d '\r')
if [ -z "$BYNAME" ]; then
  log "FATAL: by-name directory not found - aborting"
  exit 1
fi
log "by-name dir: $BYNAME"

"$ADB" shell "ls -l $BYNAME" 2>&1 | tr -d '\r' > "$OUT/partitions.txt"
log "partition map saved to partitions.txt"

# --- root check ---
if ! "$ADB" shell 'su -c id' 2>/dev/null | grep -q 'uid=0'; then
  log "FATAL: su not available - cannot read raw partitions. Aborting."
  exit 1
fi
log "root: ok"

FAILED=""
for p in $PARTS; do
  DEV="$BYNAME/$p"
  if ! "$ADB" shell "[ -e $DEV ] && echo yes" 2>/dev/null | grep -q yes; then
    log "skip  $p (not present)"
    continue
  fi

  log "---- $p ----"
  HASH_DEV=$("$ADB" shell "su -c 'dd if=$DEV bs=1048576 2>/dev/null | md5sum 2>/dev/null || dd if=$DEV bs=1048576 2>/dev/null | md5'" 2>/dev/null | tr -d '\r' | awk '{print $1}')
  log "device md5: $HASH_DEV"

  "$ADB" exec-out "su -c 'dd if=$DEV bs=1048576 2>/dev/null'" 2>/dev/null | gzip -1 > "$OUT/$p.img.gz"
  RC=$?
  if [ $RC -ne 0 ] || [ ! -s "$OUT/$p.img.gz" ]; then
    log "FAIL  $p (stream rc=$RC)"
    FAILED="$FAILED $p"
    rm -f "$OUT/$p.img.gz"
    continue
  fi

  HASH_LOCAL=$(gzip -dc "$OUT/$p.img.gz" | md5sum | awk '{print $1}')
  SIZE=$(wc -c < "$OUT/$p.img.gz")
  if [ "$HASH_DEV" = "$HASH_LOCAL" ]; then
    log "OK    $p  md5 match  gz=${SIZE}B"
  else
    log "FAIL  $p  md5 MISMATCH dev=$HASH_DEV local=$HASH_LOCAL"
    FAILED="$FAILED $p"
  fi
done

log "---- summary ----"
log "failed:${FAILED:- none}"
log "files:"
ls -l "$OUT" | tee -a "$LOG"

log "backup finished"
