#!/system/bin/sh
# Device-side debloat / restore for SM-G355HN (KitKat, API 19).
# Works both in Android (with su) and in TWRP (no pm available).
#
#   sh /data/local/tmp/debloat.sh apply   /data/local/tmp/manifest.txt
#   sh /data/local/tmp/debloat.sh restore
#
# Moves APK+odex out of /system into /data/local/debloat-backup, preserving the
# original path, and records every move in a log for a byte-exact rollback.
#
# NOTE: this device's toolbox has NO awk/sed/basename/dirname/head/printf.
# Only shell builtins, grep, mv, mkdir, mount, sync are used on purpose.
set -u

MODE="${1:-}"
MANIFEST="${2:-}"
BK=/data/local/debloat-backup
LOG=$BK/debloat.log
NL='
'

say() { echo "== $* =="; }

mount_rw() {
  mount | grep -q " /system " || mount /system 2>/dev/null
  mount -o rw,remount /system 2>/dev/null || true
  mount | grep " /system "
}

mount_data() {
  mount | grep -q " /data " || mount /data 2>/dev/null
  mount | grep " /data "
}

# first line only, without head
firstline() {
  _v="$1"
  echo "${_v%%$NL*}"
}

case "$MODE" in
apply)
  [ -f "$MANIFEST" ] || { echo "FATAL: manifest $MANIFEST missing"; exit 1; }
  mkdir -p "$BK" || exit 1
  say "system"; mount_rw
  say "data";   mount_data
  : > "$LOG"

  moved=0; skipped=0; missing=0
  while read -r pkg; do
    case "$pkg" in ''|\#*) continue ;; esac

    path=""
    raw=$(pm path "$pkg" 2>/dev/null)
    if [ -n "$raw" ]; then
      raw=$(firstline "$raw")
      path="${raw#package:}"
    fi

    if [ -z "$path" ] && [ -f /data/local/tmp/pkgmap.txt ]; then
      while read -r mp mq; do
        if [ "$mp" = "$pkg" ]; then path="$mq"; break; fi
      done < /data/local/tmp/pkgmap.txt
    fi

    if [ -z "$path" ] || [ ! -f "$path" ]; then
      echo "MISS $pkg"; missing=$((missing+1)); continue
    fi

    rel="${path#/system/}"
    dest="$BK/$rel"
    mkdir -p "${dest%/*}" || continue

    if [ -f "$dest" ]; then
      echo "SKIP $pkg (already backed up)"; skipped=$((skipped+1)); continue
    fi

    if cp -f "$path" "$dest" && rm -f "$path"; then
      echo "$pkg $path" >> "$LOG"
      moved=$((moved+1))
      odex="${path%.apk}.odex"
      if [ -f "$odex" ]; then
        cp -f "$odex" "$BK/${rel%.apk}.odex" && rm -f "$odex" && echo "$pkg $odex" >> "$LOG"
      fi
      echo "MOVED $pkg -> $dest"
    else
      echo "FAIL $pkg"
    fi
  done < "$MANIFEST"

  sync
  say "summary"
  echo "moved=$moved skipped=$skipped missing=$missing"
  echo "backup dir: $BK"
  ;;

restore)
  [ -f "$LOG" ] || { echo "FATAL: $LOG missing, nothing to restore"; exit 1; }
  say "system"; mount_rw
  say "data";   mount_data

  ok=0; bad=0
  while read -r pkg orig; do
    case "$pkg" in ''|\#*) continue ;; esac
    rel="${orig#/system/}"
    src="$BK/$rel"
    if [ ! -f "$src" ]; then echo "MISS $src"; bad=$((bad+1)); continue; fi
    mkdir -p "${orig%/*}"
    if cp -f "$src" "$orig" && rm -f "$src"; then
      echo "RESTORED $pkg -> $orig"; ok=$((ok+1))
      osrc="$BK/${rel%.apk}.odex"
      [ -f "$osrc" ] && cp -f "$osrc" "${orig%.apk}.odex" && rm -f "$osrc"
    else
      echo "FAIL $pkg"; bad=$((bad+1))
    fi
  done < "$LOG"

  sync
  say "summary"
  echo "restored=$ok failed=$bad"
  ;;

*)
  echo "usage: sh $0 apply <manifest> | restore"
  exit 1
  ;;
esac
