#!/system/bin/sh
# omnicoder-render.sh — regenerate the omnicoder surface from LIVE LOCAL state.
#
# Reads ONLY local fabric files (never the network, never any remote input), seds
# the live values into omnicoder.template.html, and atomically replaces
# omnicoder.html. Held-safe: no payload, no eval, no exec of anything dynamic.
# NO node, NO json.
ROOT=/sdcard/Asolaria
TEMPLATE=$ROOT/omnicoder.template.html
OUT=$ROOT/omnicoder.html
TMP=$ROOT/.omnicoder.html.tmp
RECEIPTS=$ROOT/8byte-receipts.hbp
INBOX=$ROOT/_auto_inbox
AUDITDIR=$ROOT/omnicoder
AUDIT=$AUDITDIR/omnicoder-render.hbp

[ -r "$TEMPLATE" ] || { echo "render: missing template $TEMPLATE" >&2; exit 1; }
mkdir -p "$AUDITDIR"

# --- live local state (local files only) ---
RECEIPTS_N=$(wc -l < "$RECEIPTS" 2>/dev/null | tr -d ' '); [ -n "$RECEIPTS_N" ] || RECEIPTS_N=0
INBOX_N=$(ls "$INBOX" 2>/dev/null | wc -l | tr -d ' ')
SER=$(getprop ro.serialno 2>/dev/null)
HOST_PID=$(pgrep -f "$ROOT/8byte-host.sh" 2>/dev/null | head -1)
UPDATED=$(date +%Y-%m-%dT%H:%M:%S)

# handle8 tokens from the latest 60 receipt rows (real recent traffic, 16-hex each)
HLIST=$(tail -n 60 "$RECEIPTS" 2>/dev/null | sed -n 's/.*handle8=\([0-9a-f]\{16\}\).*/\1/p')
HANDLE_COUNT=$(printf '%s\n' "$HLIST" | grep -c .)
# build  "h1","h2",...  (no trailing comma); empty -> empty array, valid JS
HANDLES=$(printf '%s\n' "$HLIST" | awk 'NF{printf "%s\"%s\"",(c++?",":""),$0}')
# newest receipt's handle8
LAST=$(printf '%s\n' "$HLIST" | grep . | tail -n 1)

# --- render: sed tokens into a fresh html, atomic replace ---
# Delimiter ~ ; none of the values contain ~, and HANDLES has no / & \ | chars.
sed \
 -e "s~@@RECEIPTS@@~$RECEIPTS_N~g" \
 -e "s~@@INBOX@@~$INBOX_N~g" \
 -e "s~@@SER@@~$SER~g" \
 -e "s~@@HOST_PID@@~$HOST_PID~g" \
 -e "s~@@LAST@@~$LAST~g" \
 -e "s~@@UPDATED@@~$UPDATED~g" \
 -e "s~@@HANDLES@@~$HANDLES~g" \
 "$TEMPLATE" > "$TMP" && mv "$TMP" "$OUT"

# --- audit row (HBP, never json) ---
echo "EVT-OMNICODER-RENDER|ts=$UPDATED|host=$SER|receipts=$RECEIPTS_N|inbox=$INBOX_N|handles=$HANDLE_COUNT|json=0" >> "$AUDIT"
