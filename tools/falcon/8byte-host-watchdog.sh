#!/system/bin/sh
# 8byte-host-watchdog.sh v7 - omnicoder: top=HBP status, bottom=3D WORLD-MODEL (cube3 city + prime cylinders + SUP/HRM/MTP/GNN observers). NO node.
ROOT=/sdcard/Asolaria; STATUS=$ROOT/PHONE-STATUS.txt; HTML=$ROOT/omnicoder.html
SER=$(getprop ro.serialno 2>/dev/null)
echo "$(date +%Y-%m-%dT%H:%M:%S) WATCHDOG v7 (3D world-model) start ser=$SER" >> "$ROOT/8byte-watchdog.log"
while true; do
  pgrep -f 8byte-host.sh >/dev/null 2>&1 || nohup sh "$ROOT/8byte-host.sh" >/dev/null 2>&1 &
  for P in 4781 8789; do pgrep -f "omnicoder-ncserver.sh $P" >/dev/null 2>&1 || nohup sh "$ROOT/omnicoder-ncserver.sh" $P >/dev/null 2>&1 & done
  HPID=$(pgrep -f 8byte-host.sh|head -1); WPID=$(pgrep -f 8byte-host-watchdog.sh|head -1)
  INBOX=$(ls "$ROOT/_auto_inbox" 2>/dev/null|wc -l); RECV=$(cat "$ROOT/8byte-receipts.ndjson" 2>/dev/null|wc -l); TS=$(date +%Y-%m-%dT%H:%M:%S)
  R1=$(tail -n 1 "$ROOT/8byte-receipts.ndjson" 2>/dev/null); LH=$(echo "$R1"|sed -n 's/.*"handle8":"\([^"]*\)".*/\1/p')
  S1=$(tail -n 1 "$ROOT/8byte-supervisor.ndjson" 2>/dev/null)
  RE=$(echo "$S1"|sed -n 's/.*"real":"\([^"]*\)".*/\1/p'); RF=$(echo "$S1"|sed -n 's/.*"self_reflect":"\([^"]*\)".*/\1/p')
  FA=$(echo "$S1"|sed -n 's/.*"ask_fabric":"\([^"]*\)".*/\1/p'); P0=$(echo "$S1"|sed -n 's/.*"fabric_pid0":"\([^"]*\)".*/\1/p')
  HANDLES=$(tail -n 48 "$ROOT/8byte-receipts.ndjson" 2>/dev/null|sed -n 's/.*"handle8":"\([^"]*\)".*/"\1"/p'|tr '\n' ',')
  echo "ASOLARIA OMNICODER ser=$SER updated=$TS host=$HPID inbox=$INBOX receipts=$RECV last=$LH" > "$STATUS" 2>/dev/null
  cat > "$HTML" <<HEOF
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=6>
<title>Asolaria</title><link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+"><link rel="apple-touch-icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Asolaria"><meta name="theme-color" content="#05070a">
<style>html,body{background:#05070a;color:#7CFC9A;font-family:ui-monospace,monospace;margin:0;padding:0}#top{padding:9px;height:40vh;overflow:auto;box-sizing:border-box}h1{color:#37E2D5;font-size:14px;letter-spacing:2px;margin:0 0 6px;display:flex;align-items:center;gap:8px}h1 img{width:24px;height:24px}.r{background:#0c1118;border-left:3px solid #37E2D5;padding:4px 7px;margin:3px 0;font-size:10px;word-break:break-all}.k{color:#37E2D5;font-weight:700}.ok{color:#7CFC9A}.d{color:#5a7;font-size:9px}#c{display:block;width:100%;height:58vh;background:#04060a;border-top:2px solid #37E2D5}</style></head><body>
<div id=top><h1><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIj48cmVjdCB3aWR0aD0iMTkyIiBoZWlnaHQ9IjE5MiIgcng9IjQyIiBmaWxsPSIjMDUwNzBhIi8+PHJlY3QgeD0iMTIiIHk9IjEyIiB3aWR0aD0iMTY4IiBoZWlnaHQ9IjE2OCIgcng9IjM0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzN0UyRDUiIHN0cm9rZS13aWR0aD0iNSIvPjx0ZXh0IHg9Ijk2IiB5PSIxMjQiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTEwIiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iIzM3RTJENSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QTwvdGV4dD48Y2lyY2xlIGN4PSIxNTAiIGN5PSIxNTAiIHI9IjEwIiBmaWxsPSIjN0NGQzlBIi8+PC9zdmc+">ASOLARIA &middot; OMNICODER</h1>
<div class=r><span class=k>DEVICE</span> |ser=$SER|updated=$TS|fmt=hbp-not-json|json=0</div>
<div class=r><span class=k>HOST</span> |host_pid=$HPID|wd=$WPID|state=<span class=ok>LIVE-held-safe</span>|json=0</div>
<div class=r><span class=k>FLOW</span> |inbox=$INBOX|receipts=$RECV|rule_of_three=on|json=0</div>
<div class=r><span class=k>TRIAD</span> |real=$RE|self_reflect=$RF|ask_fabric=$FA|sup_pid0=$P0|json=0</div>
<div class=r d>3D world-model below &middot; pixels-first &middot; process_launch=0 &middot; NOT free supercompute &middot; IT is slices</div></div>
<canvas id=c></canvas>
<script>
var H=[$HANDLES];var T=["$RE","$RF","$FA","$P0"];var MET={inbox:$INBOX,recv:$RECV};
var cv=document.getElementById('c'),g=cv.getContext('2d');
function sz(){cv.width=window.innerWidth;cv.height=Math.floor(window.innerHeight*0.58);}sz();window.addEventListener('resize',sz);
function hx(h,a,b){return parseInt(((h||'0')+'00000000').slice(a,b),16)||0;}
function isP(n){if(n<2)return 0;for(var i=2;i*i<=n;i++){if(n%i==0)return 0;}return 1;}
var t=0;
function proj(x,y,z,th,W,Hh){var cx=W/2,cy=Hh*0.6,s=Math.min(W,Hh)/2.4;var X=x*Math.cos(th)-z*Math.sin(th),Z=x*Math.sin(th)+z*Math.cos(th);return {sx:cx+X*s,sy:cy+y*s*0.9-Z*s*0.34,d:Z};}
function draw(){var W=cv.width,Hh=cv.height,th=t/130;g.fillStyle='#04060a';g.fillRect(0,0,W,Hh);
 var N=6,cells=[];for(var gx=0;gx<N;gx++){for(var gz=0;gz<N;gz++){var idx=gx*N+gz,lit=0;for(var i=0;i<H.length;i++){if(hx(H[i],0,4)%(N*N)==idx)lit++;}cells.push({x:(gx-(N-1)/2)/N*1.7,z:(gz-(N-1)/2)/N*1.7,lit:lit,idx:idx});}}
 cells.sort(function(a,b){return proj(a.x,0,a.z,th,W,Hh).d-proj(b.x,0,b.z,th,W,Hh).d;});
 for(var c=0;c<cells.length;c++){var ce=cells[c],p=proj(ce.x,0,ce.z,th,W,Hh),sc=Math.min(W,Hh)/N/2.8;
  g.fillStyle=ce.lit?'rgba(22,168,90,'+Math.min(0.9,0.22+ce.lit*0.22)+')':'rgba(30,55,65,0.22)';g.fillRect(p.sx-sc,p.sy-sc/2,sc*2,sc);
  if(isP(ce.idx)){var hh=0.18+0.55*(ce.idx/(N*N)),top=proj(ce.x,-hh,ce.z,th,W,Hh);g.strokeStyle='#37E2D5';g.lineWidth=2;g.beginPath();g.moveTo(p.sx,p.sy);g.lineTo(top.sx,top.sy);g.stroke();g.fillStyle='#7CFC9A';g.beginPath();g.arc(top.sx,top.sy,3,0,6.3);g.fill();g.lineWidth=1;}}
 var pts=[];for(var i=0;i<H.length;i++){var ang=hx(H[i],0,4)/65535*6.283,rad=0.35+hx(H[i],4,6)/255*0.6,yy=-0.45-hx(H[i],6,8)/255*0.5;pts.push(proj(Math.cos(ang)*rad,yy,Math.sin(ang)*rad,th,W,Hh));}
 g.strokeStyle='rgba(55,226,213,0.3)';g.beginPath();for(var i=1;i<pts.length;i++){g.moveTo(pts[i-1].sx,pts[i-1].sy);g.lineTo(pts[i].sx,pts[i].sy);}g.stroke();
 for(var i=0;i<pts.length;i++){var r=2+(Math.sin(t/15+i)+1)*1.3;g.fillStyle=(i==pts.length-1)?'#7CFC9A':'#37E2D5';g.beginPath();g.arc(pts[i].sx,pts[i].sy,r,0,6.3);g.fill();}
 var ctr=proj(0,-0.35,0,th,W,Hh),obs=[['SUP',-1.3,-1,-1.3,'#7CFC9A'],['HRM',1.3,-1,-1.3,'#ffd166'],['MTP',1.3,-1,1.3,'#ff7ad5'],['GNN',-1.3,-1,1.3,'#37E2D5']];
 for(var o=0;o<obs.length;o++){var ob=obs[o],p=proj(ob[1],ob[2],ob[3],th,W,Hh);g.strokeStyle=ob[4];g.globalAlpha=0.45;g.beginPath();g.moveTo(p.sx,p.sy);g.lineTo(ctr.sx,ctr.sy);g.stroke();g.globalAlpha=1;g.fillStyle=ob[4];g.beginPath();g.arc(p.sx,p.sy,5,0,6.3);g.fill();g.font='10px monospace';g.fillText(ob[0],p.sx+7,p.sy+3);}
 g.fillStyle='#5a7';g.font='11px monospace';g.fillText('3D WORLD-MODEL pixels-first map3/cube3 city nodes='+H.length,8,15);
 g.fillText('rooms='+MET.inbox+' receipts='+MET.recv+' obs:SUP HRM MTP GNN prime-cylinders',8,30);
 t++;requestAnimationFrame(draw);}
draw();
</script></body></html>
HEOF
  sleep 6
done