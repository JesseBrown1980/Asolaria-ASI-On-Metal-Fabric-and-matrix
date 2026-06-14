#!/system/bin/sh
# lane-handler.sh — per-connection handler for the falcon lane.
# Invoked by:  nc -l [-p] 8801 /system/bin/sh /sdcard/Asolaria/lane-handler.sh
# nc wires this script's stdin AND stdout to the client socket, so reading the
# line from stdin and PRINTING the ack to stdout sends the ack straight back —
# no FIFO (mkfifo fails on /sdcard FUSE/sdcardfs). Queue-only, never exec. NO node, NO json.
IFS= read -r line
case "$line" in
  *"|json=0"*)
     f=/sdcard/Asolaria/_auto_inbox/lane_$(date +%s)_$$.hbp
     printf '%s\n' "$line" >> "$f"            # queue only, never exec
     rh=$(printf '%s' "$line" | md5sum | cut -c1-16)
     printf 'EVT-LANE-ACK|ts=%s|host=%s|accepted=1|row_hash=%s|json=0\n' \
            "$(date +%Y-%m-%dT%H:%M:%S)" "$(getprop ro.serialno)" "$rh" ;;
  *) printf 'ERR|reason=not-hbp|json=0\n' ;;
esac
