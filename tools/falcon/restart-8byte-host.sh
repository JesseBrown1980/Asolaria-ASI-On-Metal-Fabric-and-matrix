#!/system/bin/sh
# Restart only the 8-byte host process, not the watchdog. sh, NO node.
ROOT=${ASOLARIA_ROOT:-/sdcard/Asolaria}
LOG=$ROOT/8byte-host.log
mkdir -p "$ROOT"
for p in $(pgrep -f "$ROOT/8byte-host.sh" 2>/dev/null); do
  [ "$p" = "$$" ] && continue
  kill "$p" 2>/dev/null
done
rm -rf "$ROOT/.8byte-host.lock" 2>/dev/null
nohup sh "$ROOT/8byte-host.sh" >/dev/null 2>&1 &
echo "$(date +%Y-%m-%dT%H:%M:%S) restart-8byte-host launched pid=$! root=$ROOT" >> "$LOG"
