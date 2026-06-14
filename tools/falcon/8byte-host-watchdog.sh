#!/system/bin/sh
# 8byte-host-watchdog.sh - keep the node-free 8-byte host alive (crash-resilience). adb-launchable, NO node.
ROOT=/sdcard/Asolaria
echo "$(date +%Y-%m-%dT%H:%M:%S) WATCHDOG start ser=$(getprop ro.serialno 2>/dev/null)" >> "$ROOT/8byte-watchdog.log"
while true; do
  if ! pgrep -f 8byte-host.sh >/dev/null 2>&1; then
    nohup sh "$ROOT/8byte-host.sh" >/dev/null 2>&1 &
    echo "$(date +%Y-%m-%dT%H:%M:%S) respawned 8byte-host" >> "$ROOT/8byte-watchdog.log"
  fi
  sleep 20
done