#!/system/bin/sh
# 8byte-host.sh v3 — phone-native 8-byte host (sh, NO node). INSTANT-LIVE:
# newest-first scan + break on first already-seen = O(new) per loop, no backlog churn.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; LOG=$ROOT/8byte-host.log
RECV=$ROOT/8byte-receipts.ndjson; SEEN=$ROOT/.8byte-seen
SER=$(getprop ro.serialno 2>/dev/null)
mkdir -p "$INBOX"
ls "$INBOX" > "$SEEN" 2>/dev/null
echo "$(date +%Y-%m-%dT%H:%M:%S) 8BYTE-HOST v3 start ser=$SER newest-first live" >> "$LOG"
while true; do
  for f in $(ls -t "$INBOX" 2>/dev/null); do
    p="$INBOX/$f"; [ -f "$p" ] || continue
    grep -qxF "$f" "$SEEN" 2>/dev/null && break
    echo "$f" >> "$SEEN"
    h=$(md5sum "$p" 2>/dev/null | cut -c1-16)
    echo "{\"ts\":\"$(date +%Y-%m-%dT%H:%M:%S)\",\"host\":\"$SER\",\"handle8\":\"$h\",\"msg\":\"$f\",\"state\":\"received_held_safe\"}" >> "$RECV"
    echo "$(date +%Y-%m-%dT%H:%M:%S) LIVE $f handle8=$h" >> "$LOG"
  done
  sleep 3
done