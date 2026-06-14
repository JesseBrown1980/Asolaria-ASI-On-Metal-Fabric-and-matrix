#!/system/bin/sh
# Node-free toybox-nc loopback HTTP server for the scientific voxel atlas.
# Serves /sdcard/Asolaria/atlas.html on :8790 (keeps the v10 omnicoder on :8789).
HTML=/sdcard/Asolaria/atlas.html
PORT=8790
while true; do
  { printf 'HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n'; cat "$HTML"; } | nc -l -p "$PORT" 2>>/sdcard/Asolaria/atlas-nc.log
done
