#!/system/bin/sh
# 8byte-host.sh v6-BOSS — restart-safe queue drain + RULE-OF-THREE agent stack per message.
# Per message: 3 agents (1 real, 1 self-reflect, 1 ask-fabric), 8-byte handle each; supervisor sees all three;
# collapse to a 0-byte fabric PID (an address, no live RAM). NO exec, NO spawn = held-safe. sh, NO node. Any device.
ROOT=${ASOLARIA_ROOT:-/sdcard/Asolaria}; INBOX=$ROOT/_auto_inbox; DONE=$ROOT/_auto_processed; LOG=$ROOT/8byte-host.log
RECV=$ROOT/8byte-receipts.hbp; SUPV=$ROOT/8byte-supervisor.hbp
LOCK=$ROOT/.8byte-host.lock; SLEEP=${ASOLARIA_SLEEP:-3}; ONCE=${ASOLARIA_ONCE:-0}
SER=$(getprop ro.serialno 2>/dev/null)
mkdir -p "$INBOX" "$DONE"
if mkdir "$LOCK" 2>/dev/null; then
  echo "$$" > "$LOCK/pid" 2>/dev/null
else
  OLD=$(cat "$LOCK/pid" 2>/dev/null)
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "$(date +%Y-%m-%dT%H:%M:%S) 8BYTE-HOST already-running pid=$OLD ser=$SER" >> "$LOG"
    exit 0
  fi
  rm -rf "$LOCK" 2>/dev/null
  mkdir "$LOCK" 2>/dev/null || exit 0
  echo "$$" > "$LOCK/pid" 2>/dev/null
fi
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT INT TERM
echo "$(date +%Y-%m-%dT%H:%M:%S) 8BYTE-HOST v6-BOSS start ser=$SER restart-safe-queue-drain hidden-files-on" >> "$LOG"
h8(){ printf '%s' "$1" | md5sum | cut -c1-16; }
safe(){ printf '%s' "$1" | tr '\r\n|' '___' | cut -c1-180; }
process_one(){
  p="$1"; [ -f "$p" ] || return
  b=${p##*/}; sb=$(safe "$b")
  REAL=$(md5sum "$p" 2>/dev/null | cut -c1-16)
  [ -n "$REAL" ] || return
  REFL=$(h8 "${REAL}:self-reflect")
  FABR=$(h8 "${b}:ask-fabric")
  PID0=$(h8 "${REAL}${REFL}${FABR}")
  ts=$(date +%Y-%m-%dT%H:%M:%S); te=$(date +%s)
  echo "EVT-8BYTE-RECEIPT|ts=$ts|host=$SER|handle8=$REAL|msg=$sb|state=received_held_safe|row_hash=$REAL|json=0" >> "$RECV"
  echo "EVT-8BYTE-SUPERVISOR|ts=$ts|host=$SER|msg=$sb|real=$REAL|self_reflect=$REFL|ask_fabric=$FABR|fabric_pid0=$PID0|supervisor=sees_all_three|held_safe=1|row_hash=$PID0|json=0" >> "$SUPV"
  echo "$ts BOSS $sb real=$REAL reflect=$REFL fabric=$FABR pid0=$PID0" >> "$LOG"
  mv "$p" "$DONE/${te}_$$_${REAL}_$sb" 2>/dev/null || rm "$p" 2>/dev/null
}
while true; do
  for p in "$INBOX"/* "$INBOX"/.[!.]* "$INBOX"/..?*; do
    process_one "$p"
  done
  [ "$ONCE" = "1" ] && break
  sleep "$SLEEP"
done
