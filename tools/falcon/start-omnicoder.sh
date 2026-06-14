#!/data/data/com.termux/files/usr/bin/sh
set -u
ROOT=/sdcard/Asolaria
APP=$ROOT/omnicoder
LOG=$APP/omnicoder.log
PID=$APP/omnicoder.pid
PORT=${OMNICODER_PORT:-8789}
mkdir -p "$APP"
if [ -f "$PID" ]; then
  OLD=$(cat "$PID" 2>/dev/null || true)
  if [ -n "$OLD" ]; then kill "$OLD" 2>/dev/null || true; fi
fi
# acer direct-edit 2026-06-14: run v2 (newer) + FULLY DETACHED stdio (setsid + </dev/null + append)
# fixes node v26 "node::ResetStdio errno 9 (EBADF)" + v8 HandleScope crash on parent-shell exit.
setsid node "$APP/omnicoder-server-v2.mjs" </dev/null >> "$LOG" 2>&1 &
echo $! > "$PID"
sleep 2
echo "OMNICODER v2 started pid=$(cat "$PID") url=http://127.0.0.1:$PORT/"
tail -n 20 "$LOG" 2>/dev/null || true