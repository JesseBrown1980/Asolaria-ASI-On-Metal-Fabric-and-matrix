#!/system/bin/sh
# ORGAN GULP — GC at 2000 (gulp) / 50000 (super-gulp). Keeps the 8-byte sh host loop fast. NO node.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; G=2000; SG=50000; LOG=$ROOT/organs/gulp/gulp.hbp
toybox mkdir -p "$ROOT/organs/gulp"
while true; do
  N=$(toybox ls "$INBOX" 2>/dev/null | toybox wc -l)
  if [ "$N" -ge "$SG" ]; then TS=$(toybox date +%s); toybox mv "$INBOX" "$ROOT/_super_gulp_$TS" 2>/dev/null; toybox mkdir -p "$INBOX"; echo "SUPERGULP|n=$N|ts=$TS|json=0" >> "$LOG"
  elif [ "$N" -ge "$G" ]; then TS=$(toybox date +%s); D="$ROOT/_gulp_$TS"; toybox mkdir -p "$D"; toybox ls "$INBOX" 2>/dev/null | toybox head -n "$G" | while IFS= read -r f; do toybox mv "$INBOX/$f" "$D/" 2>/dev/null; done; echo "GULP|moved=$G|n_was=$N|ts=$TS|json=0" >> "$LOG"; fi
  toybox sleep 20
done
