#!/system/bin/sh
# ORGAN GNN — route edge-features to the TRAINED EdgeLevelGNN on acer (phone has no torch). NO node.
# Reads edges (HBP) from organs/gnn/_in, POSTs to the trained model, writes scores to organs/gnn/_out.
ROOT=/sdcard/Asolaria; IN=$ROOT/organs/gnn/_in; OUT=$ROOT/organs/gnn/_out; TRAINED=http://192.168.1.50:4792/infer
toybox mkdir -p "$IN" "$OUT"
while true; do
  toybox ls "$IN" 2>/dev/null | while IFS= read -r e; do
    [ -n "$e" ] || continue
    R=$(toybox timeout 6 toybox wget -qO- --post-file="$IN/$e" "$TRAINED" 2>/dev/null)
    echo "GNN-ROUTE|edge=$e|trained=$TRAINED|score_raw=$R|json=0" >> "$OUT/scores.hbp"; toybox rm -f "$IN/$e"
  done
  toybox sleep 8
done
