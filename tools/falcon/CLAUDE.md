# Falcon — Asolaria Fabric Node (remote-controlled drive)

## What this is
Falcon (SM-S721U1, serial R5CXA4MGQXV) is an Asolaria fabric PROCESSING NODE, currently
USB-connected to acer (a drive here), to go remote/aerial later. acer and the fabrics
REMOTE-CONTROL Falcon by files. That is the point.

## How it is driven (AI-native — NOT a human at a terminal, NOT node-per-op)
- DIRECT FILE MANAGER: acer pulls / edits / pushes files on this device (adb push/pull).
  No Termux keystrokes. No spinning a new `node` per operation (way too expensive).
- 8-BYTE HOST-PROCESS REMOTE CONTROL: each agent is an 8-byte handle. Remote control =
  acer/the-fabric writes a tiny message-file; the ONE persistent host reads it and activates
  the 8-byte host-process. Cheap: one persistent host + tiny file messages, never node-per-message.

## The persistent host (omnicoder) — fixed
- /sdcard/Asolaria/omnicoder/omnicoder-server-v2.mjs  (one persistent host; lib/ complete:
  hyperbehcs-core.cjs, zeta-process.mjs, hrm-slow-fast.mjs, mtp-heads.mjs, primes.mjs, hilbert.mjs).
- start-omnicoder.sh: runs v2 + setsid + </dev/null + append-log (fixes node v26 EBADF/HandleScope).
- falcon-omnicoder-persistent.sh: respawn watchdog so the host stays up permanently.
- Watches /sdcard/Asolaria/_auto_inbox; processes message-files through
  hookwall -> forward_gnn -> reverse_gain_gnn -> omnishannon -> omniwhite_room -> gc, held-safe.

## SEQUENCE (do not skip)
1. The surface must WORK first: program files present + correct + host running.
   Never write a message to a broken / unqueryable surface and expect interaction.
2. THEN write 8-byte message-files for the host to process.

## Held-safe
fail_closed, append_only, apex-gated. native_android_codex=false -> heavy coding routes to the
acer/liris backend; Falcon runs the cheap 8-byte host + receives remote control by files.

## Migration
Migrating the fabric TO the phone via the file manager, phone-as-drive here, until remote/aerial
again. The same method onboards Felipe's Aether and the S22 Ultra next; then "ask the fabric"
becomes "ask many fabrics."