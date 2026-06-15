#!/system/bin/sh
# lane-handler.sh — per-connection HELD-SAFE verb dispatcher for the falcon lane.
# Invoked by:  nc -l [-p] 8801 /system/bin/sh /sdcard/Asolaria/lane-handler.sh
# nc wires this script's stdin AND stdout to the client socket, so reading the
# line from stdin and PRINTING the ack to stdout sends the ack straight back —
# no FIFO (mkfifo fails on /sdcard FUSE/sdcardfs). NO node, NO json.
#
# HELD-SAFE: the remote line is NEVER passed to sh/eval. Only ONE whitelisted verb
# (EVT-OMNICODER-REFRESH) triggers an action, and that action is a FIXED-PATH local
# render script (reads local state only). Everything else keeps the committed
# phone-to-phone lane behavior EXACTLY (queue-only, never exec).
IFS= read -r line
case "$line" in
  "EVT-OMNICODER-REFRESH|"* )
     # WHITELISTED verb (matched BEFORE the generic |json=0 case, which it also contains).
     # Run the FIXED local render script — the payload is NEVER exec'd/eval'd/queued.
     sh /sdcard/Asolaria/omnicoder-render.sh >/dev/null 2>&1
     rc=$(wc -l < /sdcard/Asolaria/8byte-receipts.hbp 2>/dev/null | tr -d ' ')
     ib=$(ls /sdcard/Asolaria/_auto_inbox 2>/dev/null | wc -l | tr -d ' ')
     printf 'EVT-OMNICODER-ACK|ts=%s|host=%s|refreshed=1|receipts=%s|inbox=%s|json=0\n' \
            "$(date +%Y-%m-%dT%H:%M:%S)" "$(getprop ro.serialno)" "$rc" "$ib" ;;
  *"|json=0"*)
     f=/sdcard/Asolaria/_auto_inbox/lane_$(date +%s)_$$.hbp
     printf '%s\n' "$line" >> "$f"            # queue only, never exec
     rh=$(printf '%s' "$line" | md5sum | cut -c1-16)
     printf 'EVT-LANE-ACK|ts=%s|host=%s|accepted=1|row_hash=%s|json=0\n' \
            "$(date +%Y-%m-%dT%H:%M:%S)" "$(getprop ro.serialno)" "$rh" ;;
  *) printf 'ERR|reason=not-hbp|json=0\n' ;;
esac
