#!/system/bin/sh
# 8byte-host.sh — phone-native 8-byte host process (pure /system/bin/sh, NO node).
# acer/the-fabric remote-control by writing message-files into _auto_inbox; this host
# emits an 8-byte handle receipt per new message, held-safe (receive+log, no exec).
ROOT=/sdcard/Asolaria
INBOX=$ROOT/_auto_inbox
LOG=$ROOT/8byte-host.log
RECV=$ROOT/8byte-receipts.ndjson
SEEN=$ROOT/.8byte-seen
SER=$(getprop ro.serialno 2>/dev/null)
mkdir -p "$INBOX"
[ -f "$SEEN" ] || : > "$SEEN"
echo "$(date +%Y-%m-%dT%H:%M:%S) 8BYTE-HOST start ser=$SER" >> "$LOG"
while true; do
  for f in "$INBOX"/*; do
    [ -f "$f" ] || continue
    b=${f##*/}
    grep -q "^$b$" "$SEEN" 2>/dev/null && continue
    echo "$b" >> "$SEEN"
    h=$(md5sum "$f" 2>/dev/null | cut -c1-16)
    echo "{\"ts\":\"$(date +%Y-%m-%dT%H:%M:%S)\",\"host\":\"$SER\",\"handle8\":\"$h\",\"msg\":\"$b\",\"state\":\"received_held_safe\"}" >> "$RECV"
    echo "$(date +%Y-%m-%dT%H:%M:%S) processed $b handle8=$h" >> "$LOG"
  done
  sleep 5
done