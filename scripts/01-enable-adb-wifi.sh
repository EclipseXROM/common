#!/bin/sh
# Enable ADB over Wi-Fi on a ROOTED device, run ON THE PHONE (Terminal Emulator / adb shell).
# Use only if the USB port or cable cannot carry data.
# Rollback: setprop service.adb.tcp.port -1 ; stop adbd ; start adbd
set -u
echo "== before =="
getprop service.adb.tcp.port
getprop persist.adb.tcp.port

echo "== enabling tcp 5555 =="
su -c 'setprop service.adb.tcp.port 5555; stop adbd; start adbd' || {
  echo "su failed - is the device really rooted?"; exit 1; }

sleep 2
echo "== after =="
getprop service.adb.tcp.port
echo "== device IP =="
ip -f inet addr show 2>/dev/null | grep -w inet || ifconfig 2>/dev/null | grep -w inet
echo
echo "Now on the PC run:"
echo "  tools/platform-tools/adb.exe connect <PHONE_IP>:5555"
