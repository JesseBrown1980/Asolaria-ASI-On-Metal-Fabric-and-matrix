#!/system/bin/sh
# falcon-lane-receiver.sh — LAN front door for the held-safe 8byte-host.
#
# Core (built by Falcon's Claude): listen TCP 8801; per connection toybox nc runs
# lane-handler.sh with stdin AND stdout wired to the client socket (trailing-COMMAND
# form), the handler reads ONE HBP line, queues it to _auto_inbox for the v6 host,
# and prints the ack back to the client. NO FIFO (mkfifo fails on /sdcard FUSE).
# NEVER execs the payload. NO node, NO json.
#
# Hardening (acer): single-instance lock + fast-exit backoff so a busy port can
# never fork-bomb the loop, and a stale double-launch can never hold 8801.
# Set NCARGS explicitly (e.g. NCARGS="-l 8801") to skip listen-syntax detection.
ROOT=/sdcard/Asolaria
INBOX=$ROOT/_auto_inbox
PORT=8801
NC=${NC:-nc}
HANDLER=$ROOT/lane-handler.sh
LOG=$ROOT/falcon-lane-receiver.log
LOCK=$ROOT/.lane-receiver.lock
mkdir -p "$INBOX"

# --- single-instance lock (dir-based; sdcard supports dirs, just not FIFOs) ---
if mkdir "$LOCK" 2>/dev/null; then
  echo "$$" > "$LOCK/pid" 2>/dev/null
else
  OLD=$(cat "$LOCK/pid" 2>/dev/null)
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "$(date +%Y-%m-%dT%H:%M:%S) lane-receiver already-running pid=$OLD" >> "$LOG"
    exit 0
  fi
  rm -rf "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
  echo "$$" > "$LOCK/pid" 2>/dev/null
fi
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT INT TERM

# --- listen form: toybox needs the port via -p (a bare positional port is the
# bug that fork-bombed). -L = persistent server that backgrounds each incoming
# connection, so a single nc serves forever with no per-accept respawn.
# Verified on toybox 0.8.12-android. Override via NCARGS env for a different nc.
NCARGS=${NCARGS:--L -p $PORT}
echo "$(date +%Y-%m-%dT%H:%M:%S) lane-receiver start pid=$$ ncargs='$NCARGS'" >> "$LOG"

# --- serve loop: nc runs the handler per connection, socket-wired -----------
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
      echo "$(date +%Y-%m-%dT%H:%M:%S) lane-receiver abort: nc fast-exit x$fails (port busy?)" >> "$LOG"
      exit 1
    fi
  else
    fails=0
  fi
done
