#!/bin/sh
# Phase 0 recon - READ ONLY. Writes nothing to the device.
# Usage: sh scripts/00-recon.sh
set -u

ROOT_DIR="${MK_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADB="$ROOT_DIR/tools/platform-tools/adb.exe"
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$ROOT_DIR/recon/$STAMP"

mkdir -p "$OUT" || exit 1

say() { printf '\n===== %s =====\n' "$1"; }

run() {
  name="$1"; shift
  say "$name"
  printf '$ %s\n' "$*"
  "$@" 2>&1
  printf '\n'
}

{
  say "adb devices"
  "$ADB" devices -l 2>&1

  say "device state"
  "$ADB" get-state 2>&1

  say "identity"
  "$ADB" shell 'id; echo; uname -a; echo; cat /proc/version' 2>&1

  say "getprop (full)"
  "$ADB" shell getprop 2>&1

  say "selected props"
  "$ADB" shell 'for p in ro.product.model ro.product.name ro.product.device ro.product.board ro.build.version.release ro.build.version.sdk ro.build.id ro.build.display.id ro.build.fingerprint ro.bootloader ro.baseband ro.serialno ro.secure ro.debuggable ro.build.type ro.build.tags ro.product.manufacturer ro.product.brand; do printf "%-32s = %s\n" "$p" "$(getprop $p)"; done' 2>&1

  say "cpu / ram"
  "$ADB" shell 'cat /proc/cpuinfo; echo; cat /proc/meminfo | head -20' 2>&1

  say "storage"
  "$ADB" shell 'df -h 2>/dev/null || df' 2>&1

  say "mounts"
  "$ADB" shell 'mount' 2>&1

  say "partitions (/proc/partitions)"
  "$ADB" shell 'cat /proc/partitions' 2>&1

  say "by-name symlinks"
  "$ADB" shell 'ls -l /dev/block/platform/*/by-name 2>/dev/null; ls -l /dev/block/platform/*/*/by-name 2>/dev/null; ls -l /dev/block/by-name 2>/dev/null' 2>&1

  say "block devices"
  "$ADB" shell 'ls -l /dev/block/ 2>/dev/null' 2>&1

  say "/system writability (read-only probe)"
  "$ADB" shell 'grep -E " /system " /proc/mounts; echo "---"; touch /system/.probe 2>&1 && { echo "WRITABLE"; rm -f /system/.probe; } || echo "NOT WRITABLE (expected on stock)"' 2>&1

  say "root / su"
  "$ADB" shell 'which su; su -c id 2>&1; echo "su_exit=$?"' 2>&1

  say "installed packages (pm list packages -f)"
  "$ADB" shell pm list packages -f 2>&1

  say "packages -s (system) count"
  "$ADB" shell 'pm list packages -s | wc -l; pm list packages -3 | wc -l' 2>&1

  say "disabled packages"
  "$ADB" shell 'pm list packages -d' 2>&1

  say "recovery / boot hints"
  "$ADB" shell 'ls -l /system/recovery-from-boot.p /system/etc/recovery-resource.dat 2>&1; getprop ro.boot.mode; getprop ro.boot.emmc; getprop ro.boot.bootloader' 2>&1

  say "selinux / security"
  "$ADB" shell 'getenforce 2>&1; getprop ro.boot.selinux' 2>&1

  say "uptime / battery"
  "$ADB" shell 'uptime; dumpsys battery 2>/dev/null | head -12' 2>&1
} > "$OUT/recon.txt" 2>&1

say "DONE"
echo "Output saved to: $OUT/recon.txt"
wc -l "$OUT/recon.txt" 2>/dev/null
