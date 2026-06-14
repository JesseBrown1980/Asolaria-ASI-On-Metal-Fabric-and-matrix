#!/system/bin/sh
# ORGAN HOOKWALL — classify each new HBP entry (uniform-entry) before the trio. Observer, NO mutate. NO node.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; OUT=$ROOT/organs/hookwall/hookwall.hbp; SEEN=$ROOT/organs/hookwall/.seen
toybox mkdir -p "$ROOT/organs/hookwall"; toybox ls "$INBOX" > "$SEEN" 2>/dev/null
while true; do
  toybox ls "$INBOX" 2>/dev/null | toybox grep -vxFf "$SEEN" 2>/dev/null | while IFS= read -r b; do
    [ -n "$b" ] || continue; K=$(toybox head -n1 "$INBOX/$b" 2>/dev/null | toybox cut -d'|' -f1)
    echo "HOOKWALL-CLASSIFY|msg=$b|key=$K|class=uniform-entry|observer=1|json=0" >> "$OUT"; echo "$b" >> "$SEEN"
  done
  toybox sleep 5
done
