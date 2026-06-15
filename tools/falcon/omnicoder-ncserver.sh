#!/system/bin/sh
# omnicoder-ncserver.sh — node-free HTTP server for the omnicoder UI (toybox nc).
#
# FIX: was  { printf header; cat html; } | nc -l -p PORT  which cat'd the body
# BEFORE a client connected -> first fetch served the PREVIOUS iteration (stale).
# Now mirrors falcon-lane-receiver.sh: persistent -L -p server runs a per-connection
# handler (omnicoder-serve.sh) that cats the CURRENT file after connect. Read-only.
# Same single-instance lock + fast-exit backoff shape. NO node, NO json. Takes a
# PORT arg (default 4781; we also run :8789).
ROOT=/sdcard/Asolaria
PORT=${1:-4781}
NC=${NC:-nc}
HANDLER=$ROOT/omnicoder-serve.sh
LOG=$ROOT/omnicoder-ncserver.log
LOCK=$ROOT/.omnicoder-ncserver-$PORT.lock

# --- per-port single-instance lock (dir-based; sdcard supports dirs, not FIFOs) ---
if mkdir "$LOCK" 2>/dev/null; then
  echo "$$" > "$LOCK/pid" 2>/dev/null
else
  OLD=$(cat "$LOCK/pid" 2>/dev/null)
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "$(date +%Y-%m-%dT%H:%M:%S) ncserver already-running port=$PORT pid=$OLD" >> "$LOG"
    exit 0
  fi
  rm -rf "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
  echo "$$" > "$LOCK/pid" 2>/dev/null
fi
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT INT TERM

# --- listen form: toybox needs the port via -p; -L = persistent server that
# backgrounds each incoming connection, so one nc serves forever (no per-accept
# respawn). Override via NCARGS env for a different nc. ---
NCARGS=${NCARGS:--L -p $PORT}
echo "$(date +%Y-%m-%dT%H:%M:%S) ncserver start port=$PORT pid=$$ ncargs='$NCARGS'" >> "$LOG"

# --- serve loop: nc runs the handler per connection, stdout socket-wired -----
# Backoff guard: if nc returns in <1s it never bound (port busy / bad flags);
# count fast-exits and abort after 10 so we never spawn a storm.
fails=0
while true; do
  start=$(date +%s)
  "$NC" $NCARGS /system/bin/sh "$HANDLER"
  end=$(date +%s)
  if [ $((end - start)) -lt 1 ]; then
    fails=$((fails+1))
    sleep 1
    if [ "$fails" -ge 10 ]; then
      echo "$(date +%Y-%m-%dT%H:%M:%S) ncserver abort port=$PORT: nc fast-exit x$fails (port busy?)" >> "$LOG"
      exit 1
    fi
  else
    fails=0
  fi
done
