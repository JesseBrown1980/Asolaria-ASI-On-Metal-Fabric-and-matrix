#!/system/bin/sh
# 8byte-host.sh v5-BOSS — name-diff scan (mtime-independent, reliable) + RULE-OF-THREE agent stack per message.
# Per message: 3 agents (1 real, 1 self-reflect, 1 ask-fabric), 8-byte handle each; supervisor sees all three;
# collapse to a 0-byte fabric PID (an address, no live RAM). NO exec, NO spawn = held-safe. sh, NO node. Any device.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; LOG=$ROOT/8byte-host.log
RECV=$ROOT/8byte-receipts.hbp; SUPV=$ROOT/8byte-supervisor.hbp
SEEN=$ROOT/.8byte-seen; TMP=$ROOT/.8byte-cur
SER=$(getprop ro.serialno 2>/dev/null)
mkdir -p "$INBOX"; ls "$INBOX" > "$SEEN" 2>/dev/null
echo "$(date +%Y-%m-%dT%H:%M:%S) 8BYTE-HOST v5-BOSS start ser=$SER rule-of-three name-diff" >> "$LOG"
h8(){ printf '%s' "$1" | md5sum | cut -c1-16; }
while true; do
  ls "$INBOX" 2>/dev/null > "$TMP"
  grep -vxFf "$SEEN" "$TMP" 2>/dev/null | while IFS= read -r b; do
    [ -n "$b" ] || continue; p="$INBOX/$b"; [ -f "$p" ] || continue
    REAL=$(md5sum "$p" 2>/dev/null | cut -c1-16)
    REFL=$(h8 "${REAL}:self-reflect")
    FABR=$(h8 "${b}:ask-fabric")
    PID0=$(h8 "${REAL}${REFL}${FABR}")
    ts=$(date +%Y-%m-%dT%H:%M:%S)
    echo "EVT-8BYTE-RECEIPT|ts=$ts|host=$SER|handle8=$REAL|msg=$b|state=received_held_safe|row_hash=$REAL|json=0" >> "$RECV"
    echo "EVT-8BYTE-SUPERVISOR|ts=$ts|host=$SER|msg=$b|real=$REAL|self_reflect=$REFL|ask_fabric=$FABR|fabric_pid0=$PID0|supervisor=sees_all_three|held_safe=1|row_hash=$PID0|json=0" >> "$SUPV"
    echo "$ts BOSS $b real=$REAL reflect=$REFL fabric=$FABR pid0=$PID0" >> "$LOG"
    echo "$b" >> "$SEEN"
  done
  sleep 3
done