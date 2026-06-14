#!/system/bin/sh
# aether-lane-sender.sh -- push ONE HBP envelope to any host:port on the fabric.
# Phone-to-phone (raw line) OR phone-to-acer-bus (port 4947 -> HTTP POST /behcs/send-hbp).
# sh ONLY. NO node. NO json.
# Usage: sh aether-lane-sender.sh <target_ip> <port> <EVT-TYPE> <short-msg>

IP="$1"; PORT="$2"; EVT="$3"; MSG="$4"
if [ -z "$IP" ] || [ -z "$PORT" ] || [ -z "$EVT" ] || [ -z "$MSG" ]; then
  echo "usage: sh aether-lane-sender.sh <target_ip> <port> <EVT-TYPE> <short-msg>" >&2
  exit 2
fi

# Serial: spec says getprop ro.serialno. In a proot/Termux shell getprop is often
# blocked, so fall back to the serial recorded in PHONE-STATUS.txt.
SER=$(getprop ro.serialno 2>/dev/null)
[ -z "$SER" ] && SER=$(sed -n 's/.*ser=\([^ ]*\).*/\1/p' /sdcard/Asolaria/PHONE-STATUS.txt 2>/dev/null)
[ -z "$SER" ] && SER=unknown

ts=$(date +%Y-%m-%dT%H:%M:%S)
line="$EVT|ts=$ts|host=$SER|msg=$MSG|json=0"

if [ "$PORT" = "4947" ]; then
  # acer bus -- raw HTTP POST to /behcs/send-hbp
  body="$line"
  clen=$(printf '%s' "$body" | wc -c | tr -d ' ')
  printf 'POST /behcs/send-hbp HTTP/1.1\r\nHost: %s:%s\r\nContent-Type: text/plain\r\nContent-Length: %s\r\nConnection: close\r\n\r\n%s' \
    "$IP" "$PORT" "$clen" "$body" | nc -w 5 "$IP" "$PORT"
else
  # phone-to-phone receiver -- raw HBP line
  printf '%s\n' "$line" | nc -w 5 "$IP" "$PORT"
fi
