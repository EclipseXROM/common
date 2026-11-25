#!/bin/sh
# Host-side wrapper: push the device script + manifest, run it, pull the log.
#   sh scripts/10-debloat.sh apply   a-safe
#   sh scripts/10-debloat.sh apply   b-caveat
#   sh scripts/10-debloat.sh restore
set -u

ROOT_DIR="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT_DIR/tools/platform-tools/adb.exe"
MODE="${1:-}"
GROUP="${2:-}"

"$ADB" devices | grep -q "device$" || { echo "FATAL: no device in 'device' state"; exit 1; }

"$ADB" push "$ROOT_DIR/debloat/debloat.sh" /data/local/tmp/debloat.sh >/dev/null || exit 1
"$ADB" push "$ROOT_DIR/recon/pkgmap.txt" /data/local/tmp/pkgmap.txt >/dev/null || exit 1

case "$MODE" in
apply)
  [ -n "$GROUP" ] || { echo "usage: sh scripts/10-debloat.sh apply <a-safe|b-caveat>"; exit 1; }
  M="$ROOT_DIR/debloat/manifest-$GROUP.txt"
  [ -f "$M" ] || { echo "FATAL: $M missing"; exit 1; }
  "$ADB" push "$M" /data/local/tmp/manifest.txt >/dev/null || exit 1
  echo "--- running apply for $GROUP ---"
  "$ADB" shell 'su -c "sh /data/local/tmp/debloat.sh apply /data/local/tmp/manifest.txt"' 2>&1 | tr -d '\r'
  ;;
restore)
  echo "--- running restore ---"
  "$ADB" shell 'su -c "sh /data/local/tmp/debloat.sh restore"' 2>&1 | tr -d '\r'
  ;;
*)
  echo "usage: sh scripts/10-debloat.sh apply <group> | restore"
  exit 1
  ;;
esac
