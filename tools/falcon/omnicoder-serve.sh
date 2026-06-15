#!/system/bin/sh
# omnicoder-serve.sh — per-connection HTTP handler for the omnicoder UI.
# Invoked by:  nc -L -p PORT /system/bin/sh /sdcard/Asolaria/omnicoder-serve.sh
# nc wires this script's stdout to the client socket, so the cat runs AFTER the
# connection is accepted -> always the CURRENT surface (fixes the one-fetch-stale
# bug where the body was cat'd before a client connected). Read-only. NO node, NO json.
HTML=/sdcard/Asolaria/omnicoder.html
# read+discard the request line so clients don't RST
IFS= read -r _req 2>/dev/null
if [ -r "$HTML" ]; then
  LEN=$(wc -c < "$HTML")
  printf 'HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %s\r\nConnection: close\r\n\r\n' "$LEN"
  cat "$HTML"
else
  B='<!doctype html><title>404</title><h1>404</h1>'; L=$(printf '%s' "$B" | wc -c)
  printf 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: %s\r\nConnection: close\r\n\r\n%s' "$L" "$B"
fi
