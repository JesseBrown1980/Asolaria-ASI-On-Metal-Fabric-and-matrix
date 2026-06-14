#!/system/bin/sh
# 8byte-host-watchdog.sh v5 - keeps host + omnicoder nc UI-servers(4781,8789) alive + writes omnicoder.html app. NO node.
ROOT=/sdcard/Asolaria; STATUS=$ROOT/PHONE-STATUS.txt; HTML=$ROOT/omnicoder.html
SER=$(getprop ro.serialno 2>/dev/null)
echo "$(date +%Y-%m-%dT%H:%M:%S) WATCHDOG v5 (host+ncservers+omnicoder-app) start ser=$SER" >> "$ROOT/8byte-watchdog.log"
while true; do
  pgrep -f 8byte-host.sh >/dev/null 2>&1 || nohup sh "$ROOT/8byte-host.sh" >/dev/null 2>&1 &
  for P in 4781 8789; do pgrep -f "omnicoder-ncserver.sh $P" >/dev/null 2>&1 || nohup sh "$ROOT/omnicoder-ncserver.sh" $P >/dev/null 2>&1 & done
  HPID=$(pgrep -f 8byte-host.sh | head -1); WPID=$(pgrep -f 8byte-host-watchdog.sh | head -1)
  INBOX=$(ls "$ROOT/_auto_inbox" 2>/dev/null | wc -l); RECV=$(cat "$ROOT/8byte-receipts.ndjson" 2>/dev/null | wc -l)
  TS=$(date +%Y-%m-%dT%H:%M:%S); R1=$(tail -n 1 "$ROOT/8byte-receipts.ndjson" 2>/dev/null)
  LH=$(echo "$R1" | sed -n 's/.*"handle8":"\([^"]*\)".*/\1/p'); LM=$(echo "$R1" | sed -n 's/.*"msg":"\([^"]*\)".*/\1/p')
  S1=$(tail -n 1 "$ROOT/8byte-supervisor.ndjson" 2>/dev/null)
  RE=$(echo "$S1" | sed -n 's/.*"real":"\([^"]*\)".*/\1/p'); RF=$(echo "$S1" | sed -n 's/.*"self_reflect":"\([^"]*\)".*/\1/p')
  FA=$(echo "$S1" | sed -n 's/.*"ask_fabric":"\([^"]*\)".*/\1/p'); P0=$(echo "$S1" | sed -n 's/.*"fabric_pid0":"\([^"]*\)".*/\1/p')
  echo "ASOLARIA OMNICODER ser=$SER updated=$TS host=$HPID wd=$WPID inbox=$INBOX receipts=$RECV last=$LH" > "$STATUS" 2>/dev/null
  cat > "$HTML" <<HEOF
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=5>
<title>Asolaria</title><link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+"><link rel="apple-touch-icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+">
<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Asolaria"><meta name="theme-color" content="#05070a">
<style>body{background:#05070a;color:#7CFC9A;font-family:ui-monospace,monospace;margin:0;padding:14px}h1{color:#37E2D5;font-size:17px;letter-spacing:2px;margin:0 0 10px;display:flex;align-items:center;gap:10px}h1 img{width:30px;height:30px}.r{background:#0c1118;border-left:3px solid #37E2D5;padding:7px 9px;margin:5px 0;font-size:12px;word-break:break-all}.k{color:#37E2D5;font-weight:700}.ok{color:#7CFC9A}.d{color:#5a7;font-size:11px}</style></head><body>
<h1><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+">ASOLARIA &middot; OMNICODER</h1>
<div class=r><span class=k>DEVICE</span> |ser=$SER|updated=$TS|fmt=hbp-not-json|json=0</div>
<div class=r><span class=k>HOST</span> |host_pid=$HPID|watchdog_pid=$WPID|state=<span class=ok>LIVE-held-safe</span>|json=0</div>
<div class=r><span class=k>FLOW</span> |inbox=$INBOX|receipts=$RECV|rule_of_three=on|json=0</div>
<div class=r><span class=k>LAST-HANDLE</span> |h8=$LH|msg=$LM|state=received_held_safe|json=0</div>
<div class=r><span class=k>TRIAD</span> |real=$RE|self_reflect=$RF|ask_fabric=$FA|json=0</div>
<div class=r><span class=k>SUPERVISOR</span> |sees_all_three|fabric_pid0=$P0|0-byte-address|json=0</div>
<div class=r d>auto-refresh 5s &middot; process_launch=0 &middot; remote_call=gated &middot; provider_terms=apply &middot; NOT free supercompute &middot; IT is slices</div>
</body></html>
HEOF
  sleep 5
done