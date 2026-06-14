#!/system/bin/sh
# omnicoder-ncserver.sh - node-free loopback HTTP server for the omnicoder UI (toybox nc, read-only static file).
ROOT=/sdcard/Asolaria; PORT=${1:-4781}; HTML=$ROOT/omnicoder.html
echo "$(date +%Y-%m-%dT%H:%M:%S) NCSERVER start port=$PORT" >> "$ROOT/8byte-watchdog.log"
while true; do
  { printf 'HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n'; cat "$HTML" 2>/dev/null; } | nc -l -p "$PORT" >/dev/null 2>&1
done