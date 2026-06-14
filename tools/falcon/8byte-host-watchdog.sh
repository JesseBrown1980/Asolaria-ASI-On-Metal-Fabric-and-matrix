#!/system/bin/sh
# 8byte-host-watchdog.sh v8 - omnicoder: top=HBP status, bottom=REAL bh_index cylinders by 3 agent-type lanes (verified math). NO node.
ROOT=/sdcard/Asolaria; STATUS=$ROOT/PHONE-STATUS.txt; HTML=$ROOT/omnicoder.html
SER=$(getprop ro.serialno 2>/dev/null)
echo "$(date +%Y-%m-%dT%H:%M:%S) WATCHDOG v8 (real bh_index cylinders) start ser=$SER" >> "$ROOT/8byte-watchdog.log"
while true; do
  pgrep -f 8byte-host.sh >/dev/null 2>&1 || nohup sh "$ROOT/8byte-host.sh" >/dev/null 2>&1 &
  for P in 4781 8789; do pgrep -f "omnicoder-ncserver.sh $P" >/dev/null 2>&1 || nohup sh "$ROOT/omnicoder-ncserver.sh" $P >/dev/null 2>&1 & done
  HPID=$(pgrep -f 8byte-host.sh|head -1); WPID=$(pgrep -f 8byte-host-watchdog.sh|head -1)
  INBOX=$(ls "$ROOT/_auto_inbox" 2>/dev/null|wc -l); RECV=$(cat "$ROOT/8byte-receipts.ndjson" 2>/dev/null|wc -l); TS=$(date +%Y-%m-%dT%H:%M:%S)
  R1=$(tail -n 1 "$ROOT/8byte-receipts.ndjson" 2>/dev/null); LH=$(echo "$R1"|sed -n 's/.*"handle8":"\([^"]*\)".*/\1/p')
  HANDLES=$(tail -n 60 "$ROOT/8byte-receipts.ndjson" 2>/dev/null|sed -n 's/.*"handle8":"\([^"]*\)".*/"\1"/p'|tr '\n' ',')
  echo "ASOLARIA OMNICODER ser=$SER updated=$TS host=$HPID inbox=$INBOX receipts=$RECV last=$LH" > "$STATUS" 2>/dev/null
  cat > "$HTML" <<HEOF
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=6>
<title>Asolaria</title><link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+"><link rel="apple-touch-icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Asolaria"><meta name="theme-color" content="#05070a">
<style>html,body{background:#05070a;color:#7CFC9A;font-family:ui-monospace,monospace;margin:0;padding:0}#top{padding:8px;height:36vh;overflow:auto;box-sizing:border-box}h1{color:#37E2D5;font-size:13px;letter-spacing:1px;margin:0 0 5px;display:flex;align-items:center;gap:7px}h1 img{width:22px;height:22px}.r{background:#0c1118;border-left:3px solid #37E2D5;padding:4px 6px;margin:3px 0;font-size:10px;word-break:break-all}.k{color:#37E2D5;font-weight:700}.ok{color:#7CFC9A}#c{display:block;width:100%;height:62vh;background:#04060a;border-top:2px solid #37E2D5}</style></head><body>
<div id=top><h1><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+">ASOLARIA &middot; OMNICODER &middot; real bh_index cylinders</h1>
<div class=r><span class=k>DEVICE</span> |ser=$SER|updated=$TS|fmt=hbp-not-json|json=0</div>
<div class=r><span class=k>HOST</span> |host_pid=$HPID|wd=$WPID|state=<span class=ok>LIVE-held-safe</span>|json=0</div>
<div class=r><span class=k>FLOW</span> |inbox=$INBOX|receipts=$RECV|last=$LH|json=0</div>
<div class=r><span class=k>MATH</span> |bh_index=sector*3072+lane*1024+glyph|cylinder=mod6|class=p/p2/p3/pk|dist=abs(d.bh)|json=0</div></div>
<canvas id=c></canvas>
<script>
var H=[$HANDLES];
var cv=document.getElementById('c'),g=cv.getContext('2d');
function sz(){cv.width=window.innerWidth;cv.height=Math.floor(window.innerHeight*0.62);}sz();window.addEventListener('resize',sz);
function u32(h){return parseInt((h+'00000000').slice(0,8),16)>>>0;}
function bh(h){var s=u32(h);return{s:s,lane:s%3,idx:(s%113)*3072+(s%3)*1024+(s%1024)};}
function ppow(n){if(n<2)return'u';var nn=n,d=2,np=0,lk=0;while(d*d<=nn){if(nn%d===0){var c=0;while(nn%d===0){nn=Math.floor(nn/d);c++;}np++;lk=c;}d++;}if(nn>1){np++;lk=1;}if(np===1)return lk===1?'p':lk===2?'p2':lk===3?'p3':'pk';return'c';}
var COL={u:'#3a4a55',p:'#37E2D5',p2:'#7CFC9A',p3:'#ffd166',pk:'#ff7ad5',c:'#243842'};
var LANES=['SUBSCRIPTION/frozen-real','FREE opencode-real','LOGICAL-MCP tells-real'];
var t=0;
function draw(){var W=cv.width,Hh=cv.height,th=t/150;g.fillStyle='#04060a';g.fillRect(0,0,W,Hh);var lw=W/3;
 for(var L=0;L<3;L++){g.strokeStyle='rgba(55,226,213,0.16)';g.beginPath();g.moveTo(L*lw,0);g.lineTo(L*lw,Hh);g.stroke();g.fillStyle='#5a7';g.font='9px monospace';g.fillText(LANES[L],L*lw+4,Hh-22);}
 var P=[];for(var i=0;i<H.length;i++){var b=bh(H[i]);var lcx=b.lane*lw+lw/2;var a=(b.idx%6)/6*6.283+th;var rr=lw*0.32;var z=Math.sin(a)*rr;var yy=Hh*0.46-(((b.idx/6)%44)/44-0.5)*Hh*0.62;P.push({x:lcx+Math.cos(a)*rr,y:yy-z*0.3,z:z,b:b,cls:ppow(b.idx)});}
 for(var i=1;i<P.length;i++){if(P[i].b.lane!==P[i-1].b.lane)continue;var d=Math.abs(P[i].b.idx-P[i-1].b.idx);var op=d<4096?0.55:d<32768?0.3:d<131072?0.14:0.05;g.globalAlpha=op;g.strokeStyle='#37E2D5';g.lineWidth=d<4096?2:1;g.beginPath();g.moveTo(P[i-1].x,P[i-1].y);g.lineTo(P[i].x,P[i].y);g.stroke();}
 g.globalAlpha=1;g.lineWidth=1;var ord=P.map(function(p,i){return i;}).sort(function(a,b){return P[a].z-P[b].z;});
 for(var k=0;k<ord.length;k++){var p=P[ord[k]];var r=3+(Math.sin(t/16+ord[k])+1)*1.2;g.fillStyle=COL[p.cls]||'#555';if(p.b.s&1){g.fillRect(p.x-r,p.y-r,r*2,r*2);}else{g.beginPath();g.arc(p.x,p.y,r,0,6.3);g.fill();}}
 var viol=0;for(var i=1;i<P.length;i++){var gp=Math.abs(P[i].b.idx-P[i-1].b.idx)%6;if(gp!==0&&gp!==2&&gp!==4)viol++;}
 g.fillStyle='#37E2D5';g.font='bold 11px monospace';g.fillText('REAL bh_index cylinders by agent-type lane  nodes='+H.length+'  mod6-viol='+viol,8,15);
 g.fillStyle='#5a7';g.font='10px monospace';g.fillText('p/p2/p3=cyan/green/gold REAL · pk=magenta(p5/p7/p9 FOLD-PROPOSAL) · circle=logical/square=real',8,30);
 g.fillStyle='#789';g.fillText('dist=|d.bh|(1D) · emitter->8byte-host->lang(device/agent-agent/agent-human) · 200ns=spec(meas~1.7us) · frozen-slice',8,Hh-8);
 t++;requestAnimationFrame(draw);}
draw();
</script></body></html>
HEOF
  sleep 6
done