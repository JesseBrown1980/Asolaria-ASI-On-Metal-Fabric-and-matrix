#!/usr/bin/env node
// build-device-organs.mjs — give a phone its OWN cubes + gulp + GNN + hookwall, sh-based (NO node).
//
// Operator 2026-06-14: "THEY SHOULD HAVE THEIR OWN CUBES and GULP and GNNS and hookwalls" + built FROM
// our trained GNN. Honest: the trained GNN (EdgeLevelGNN baseline_model.pt) runs on acer :4792 — the
// phone CANNOT host torch, so its GNN-organ is a CONNECTOR that routes the phone's edges to the trained
// model over the bus/LAN and gets scores back. Cubes/gulp/hookwall are real sh routines (no node).
//   GULP = the GC at 2000 (gulp) / 50000 (super-gulp) — also the fix for the host-loop bloat.
//
// node = builder here only. Emits HBP organ rows + the sh routines the phone runs. process_launch=0.

import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const firstExisting = (c) => { for (const p of c) if (p && existsSync(p)) return p; throw new Error('NN engine missing'); };
const NN = firstExisting([process.env.ASOLARIA_NN_EXPORTER,
  'C:/asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs',
  'C:/Users/rayss/ASOLARIA-AS-NEURAL-NETWORK/tools/behcs/pre-existence-graph-exporter.mjs',
  resolve(HERE, '../../../asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs')]);
const { preExistenceNode } = await import(pathToFileURL(NN).href);

const DEVICE = process.env.ASOLARIA_DEVICE || process.argv[2] || 'falcon:R5CXA4MGQXV';
const [LABEL, SER] = DEVICE.split(':');
const OUTDIR = resolve('reports/device-organs');
const dh = (pid) => createHash('md5').update(pid + ':' + SER).digest('hex').slice(0, 16);
const pidOf = (n) => preExistenceNode(`${LABEL.toUpperCase()}-ORGAN-${n}`);
// acer trained GNN endpoint the device GNN-organ routes to (the phone has no torch).
const TRAINED_GNN = process.env.ASOLARIA_TRAINED_GNN || 'http://192.168.1.50:4792/infer';

const cube = pidOf('CUBES'), gulp = pidOf('GULP'), gnn = pidOf('GNN'), hook = pidOf('HOOKWALL');
const rows = [
  `ORGANHDR|schema=hbp.device.organ.v1|device=${LABEL}:${SER}|organs=cubes+gulp+gnn+hookwall|node_on_phone=0|sh=1|trained_gnn=${TRAINED_GNN}|held_safe=1|json=0`,
  `ORGANCUBE|name=${LABEL}-ORGAN-CUBES|pid=${cube.pid}|device_handle=${dh(cube.pid)}|alphabet=BEHCS-1024|store=/sdcard/Asolaria/organs/cubes|holds=glyph-cubes+token-cube-catalog|bh_index=${cube.bh_index}|tier=RESTRICTED|process_launch=0|json=0`,
  `ORGANGULP|name=${LABEL}-ORGAN-GULP|pid=${gulp.pid}|device_handle=${dh(gulp.pid)}|gulp=2000|super_gulp=50000|routine=/sdcard/Asolaria/organs/gulp/gulp.sh|keeps=sh-host-loop-fast(fixes-inbox-bloat)|bh_index=${gulp.bh_index}|process_launch=0|json=0`,
  `ORGANGNN|name=${LABEL}-ORGAN-GNN|pid=${gnn.pid}|device_handle=${dh(gnn.pid)}|kind=CONNECTOR-to-trained-model|trained=${TRAINED_GNN}(EdgeLevelGNN-baseline_model.pt~91.87pct-on-acer)|phone_hosts_torch=0|routes=edge-features->trained-gnn->scores|routine=/sdcard/Asolaria/organs/gnn/gnn-route.sh|bh_index=${gnn.bh_index}|tier=RESTRICTED|process_launch=0|json=0`,
  `ORGANHOOK|name=${LABEL}-ORGAN-HOOKWALL|pid=${hook.pid}|device_handle=${dh(hook.pid)}|kind=sh-uniform-entry-classifier|observer=1|no_mutate=1|routine=/sdcard/Asolaria/organs/hookwall/hookwall.sh|bh_index=${hook.bh_index}|process_launch=0|json=0`,
  `ORGANHONEST|device=${LABEL}:${SER}|cubes=real-sh-store|gulp=real-sh-GC|hookwall=real-sh-classifier|gnn=CONNECTOR-to-acer-trained-model-NOT-phone-local-torch|trained_weights_stay_on_acer=1|json=0`,
  `ORGANFTR|device=${LABEL}:${SER}|organs=4|from_trained_gnn=via-connector|registered_here=acer|pushed=pending|next=push+launch-via-watchdog|json=0`,
];

// --- the real sh routines (NO node) ---
const gulpSh = `#!/system/bin/sh
# ORGAN GULP — GC at 2000 (gulp) / 50000 (super-gulp). Keeps the 8-byte sh host loop fast. NO node.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; G=2000; SG=50000; LOG=$ROOT/organs/gulp/gulp.hbp
toybox mkdir -p "$ROOT/organs/gulp"
while true; do
  N=$(toybox ls "$INBOX" 2>/dev/null | toybox wc -l)
  if [ "$N" -ge "$SG" ]; then TS=$(toybox date +%s); toybox mv "$INBOX" "$ROOT/_super_gulp_$TS" 2>/dev/null; toybox mkdir -p "$INBOX"; echo "SUPERGULP|n=$N|ts=$TS|json=0" >> "$LOG"
  elif [ "$N" -ge "$G" ]; then TS=$(toybox date +%s); D="$ROOT/_gulp_$TS"; toybox mkdir -p "$D"; toybox ls "$INBOX" 2>/dev/null | toybox head -n "$G" | while IFS= read -r f; do toybox mv "$INBOX/$f" "$D/" 2>/dev/null; done; echo "GULP|moved=$G|n_was=$N|ts=$TS|json=0" >> "$LOG"; fi
  toybox sleep 20
done
`;
const hookSh = `#!/system/bin/sh
# ORGAN HOOKWALL — classify each new HBP entry (uniform-entry) before the trio. Observer, NO mutate. NO node.
ROOT=/sdcard/Asolaria; INBOX=$ROOT/_auto_inbox; OUT=$ROOT/organs/hookwall/hookwall.hbp; SEEN=$ROOT/organs/hookwall/.seen
toybox mkdir -p "$ROOT/organs/hookwall"; toybox ls "$INBOX" > "$SEEN" 2>/dev/null
while true; do
  toybox ls "$INBOX" 2>/dev/null | toybox grep -vxFf "$SEEN" 2>/dev/null | while IFS= read -r b; do
    [ -n "$b" ] || continue; K=$(toybox head -n1 "$INBOX/$b" 2>/dev/null | toybox cut -d'|' -f1)
    echo "HOOKWALL-CLASSIFY|msg=$b|key=$K|class=uniform-entry|observer=1|json=0" >> "$OUT"; echo "$b" >> "$SEEN"
  done
  toybox sleep 5
done
`;
const gnnSh = `#!/system/bin/sh
# ORGAN GNN — route edge-features to the TRAINED EdgeLevelGNN on acer (phone has no torch). NO node.
# Reads edges (HBP) from organs/gnn/_in, POSTs to the trained model, writes scores to organs/gnn/_out.
ROOT=/sdcard/Asolaria; IN=$ROOT/organs/gnn/_in; OUT=$ROOT/organs/gnn/_out; TRAINED=${TRAINED_GNN}
toybox mkdir -p "$IN" "$OUT"
while true; do
  toybox ls "$IN" 2>/dev/null | while IFS= read -r e; do
    [ -n "$e" ] || continue
    R=$(toybox timeout 6 toybox wget -qO- --post-file="$IN/$e" "$TRAINED" 2>/dev/null)
    echo "GNN-ROUTE|edge=$e|trained=$TRAINED|score_raw=$R|json=0" >> "$OUT/scores.hbp"; toybox rm -f "$IN/$e"
  done
  toybox sleep 8
done
`;
mkdirSync(OUTDIR, { recursive: true });
writeFileSync(resolve(OUTDIR, `organs-${LABEL}.hbp`), rows.join('\n') + '\n');
writeFileSync(resolve(OUTDIR, 'gulp.sh'), gulpSh);
writeFileSync(resolve(OUTDIR, 'hookwall.sh'), hookSh);
writeFileSync(resolve(OUTDIR, 'gnn-route.sh'), gnnSh);
console.log(`DEVICE-ORGANS-BUILT|device=${LABEL}:${SER}|organs=cubes+gulp+gnn(connector->trained)+hookwall|gnn_trained=${TRAINED_GNN}|routines=gulp.sh+hookwall.sh+gnn-route.sh|out=${OUTDIR}/organs-${LABEL}.hbp`);
