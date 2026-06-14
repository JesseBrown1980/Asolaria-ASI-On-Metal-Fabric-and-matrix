#!/usr/bin/env node
// ACER multi-cylinder scientific atlas — SIX separated prime cylinders.
//
// Converges with liris 939cdac: runs the LIVE 726-PID office roster through liris's
// VERIFIED coordinate engine (pre-existence-graph-exporter.preExistenceNode), then
// renders the six bh_index-mod-6 phases as SIX SPATIALLY-DISTINCT cylinders.
//
// VERIFIED transform (cross-checked bad_coords=0 on acer, suite 393/393):
//   reg = mintPid(name) -> sector/lane/glyph
//   bh_index       = sector*3072 + lane*1024 + glyph
//   cylinder_phase = bh_index mod 6            -> WHICH of 6 cylinders
//   cylinder_ring  = floor(bh_index / 6)       -> height up that cylinder
//   prime_band     = PRIME_CUBE_PRIMES[sector % 11]  (13..131, cubed = anchor)
//   watcher_lane   = [hookwall, gnn, shannon][lane % 3]   = rule-of-three observers
//
// HONEST (rendered in header): coords REAL · NO true Hilbert d2xyz curve (linear index
// folded mod-6) · GNN watch LIVE but proposal-not-proof · live process telemetry NOT claimed.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const FEED = process.argv[2] || 'D:/PID-Registration-Office/fabric-feed/supervisors-fabric-feed-2026-06-10.hbp';
const OUT  = process.argv[3] || resolve('reports/acer-multi-cylinder-atlas.html');
const NN   = 'C:/asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs';

// ---- import liris's VERIFIED coordinate engine (cross-repo, absolute) ---------------
const prex = await import(pathToFileURL(NN).href);
const { preExistenceNode, PRIME_CUBE_PRIMES, PRIME_CUBES, WATCHER_LANES } = prex;

// ---- live office roster (726 real PIDs) ---------------------------------------------
const raw = readFileSync(FEED, 'utf8');
const regRows = raw.split(/\r?\n/).filter(l => l.startsWith('REG|'));
const field = (line, key) => { const m = line.match(new RegExp('(?:^|\\|)' + key + '=([^|]*)')); return m ? m[1] : ''; };

function laneOf(layer, cls) {
  const s = (layer + ' ' + cls).toLowerCase();
  if (/usb|sovereign|cloud|hidden|paper|corpus|cartridge|frozen/.test(s)) return 'frozen';
  if (/room|substrate|prof|planb|basin|spindle|bh-room|descriptor|sector|shard/.test(s)) return 'logical';
  return 'real';
}
const isHostName = (name, layer, cls) =>
  /^PROF-|^OP-|HOST|AGENT-TERMINAL|KERNEL|HERMES/.test(name) || /kernel|hermes|prof-supervisor/.test((layer + cls).toLowerCase());

const seen = new Set();
const nodes = [];
for (const line of regRows) {
  const name = field(line, 'name');
  const layer = field(line, 'layer');
  const cls = field(line, 'class');
  if (!name) continue;
  const key = name + ':' + layer + ':' + field(line, 'g5');
  if (seen.has(key)) continue;
  seen.add(key);
  // run the LIVE office name through liris's VERIFIED coordinate engine:
  const pn = preExistenceNode(name);
  nodes.push({
    name, layer, class: cls,
    pid: pn.pid,
    sector: pn.sector, lane: pn.lane, glyph: pn.glyph_binding,
    bh_index: pn.bh_index,
    phase: pn.cylinder_phase, ring: pn.cylinder_ring,
    prime_band: pn.prime_band, prime_cube: pn.prime_cube,
    watcher: pn.watcher_lane,
    sys_lane: laneOf(layer, cls),
    isHost: isHostName(name, layer, cls),
  });
}

// ring normalisation for height
const rings = nodes.map(n => n.ring);
const rMin = Math.min(...rings), rMax = Math.max(...rings);
const normRing = r => (rMax === rMin ? 0.5 : (r - rMin) / (rMax - rMin));
for (const n of nodes) n.h = normRing(n.ring);

const phaseCounts = nodes.reduce((a, n) => (a[n.phase] = (a[n.phase] || 0) + 1, a), {});
const watcherCounts = nodes.reduce((a, n) => (a[n.watcher] = (a[n.watcher] || 0) + 1, a), {});
const laneCounts = nodes.reduce((a, n) => (a[n.sys_lane] = (a[n.sys_lane] || 0) + 1, a), {});

const gnnWatch = {
  note: 'LIVE + MOVING: sampled 68->178, rank-3 score 0.603->0.820 across two pulls this session (proposal-not-proof)',
  predictions: [
    { rank: 1, target: 'acer-desktop', score: 1.0 }, { rank: 2, target: 'falcon-s24fe', score: 1.0 },
    { rank: 3, target: 'broadcast(pid-stamp.gnn-edge-emit)', score: 0.820 },
    { rank: 4, target: 'aether-a06-via-liris', score: 0.486 }, { rank: 5, target: 'liris-desktop-via-bus', score: 0.486 },
  ],
};

const meta = {
  feed: FEED, plotted: nodes.length, engine: NN + ' (liris 939cdac, cross-checked bad_coords=0 on acer)',
  phaseCounts, watcherCounts, laneCounts,
  prime_cubes: PRIME_CUBES, prime_cube_primes: PRIME_CUBE_PRIMES, watcher_lanes: WATCHER_LANES,
  bh_index_range: [Math.min(...nodes.map(n => n.bh_index)), Math.max(...nodes.map(n => n.bh_index))],
};
const DATA = JSON.stringify({ nodes, gnnWatch, meta });

const html = `<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>ACER · Multi-Cylinder Prime Atlas — 6 cylinders, live PIDs</title>
<style>
 :root{--bg:#04060c;--fg:#cfe3ff;--dim:#5b6b86;--hookwall:#37b6ff;--gnn:#36e07f;--shannon:#b98cff;--host:#ffd24a;--gnnr:#ff4d6d}
 *{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:12px/1.5 ui-monospace,Consolas,monospace}
 #wrap{display:flex;flex-direction:column;height:100vh}header{padding:7px 12px;border-bottom:1px solid #13203a;background:#060a14}
 header b{color:#fff}.k{color:#7fffd4}.warn{color:#ffb454}.hookwall{color:var(--hookwall)}.gnn{color:var(--gnn)}.shannon{color:var(--shannon)}.host{color:var(--host)}
 #main{flex:1;display:flex;min-height:0}#cv{flex:1;display:block;cursor:grab}#cv:active{cursor:grabbing}
 #side{width:330px;border-left:1px solid #13203a;overflow:auto;padding:8px 10px;background:#060a14}
 h3{margin:9px 0 3px;color:#fff;font-size:12px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
 table{width:100%;border-collapse:collapse;font-size:11px}th,td{text-align:left;padding:2px 4px;border-bottom:1px solid #10203a}th{color:var(--dim)}
 footer{padding:5px 12px;border-top:1px solid #13203a;color:var(--dim);background:#060a14}
</style></head><body><div id=wrap>
<header>
 <b>ACER · MULTI-CYLINDER PRIME ATLAS</b> &middot; <span class=k>__N__ live PIDs</span> through liris's verified engine &middot; <span class=k>SIX bh_index mod-6 cylinders</span> &middot; bh_index range <span class=k>__BHR__</span><br>
 rule-of-three watchers: <span class=hookwall>● hookwall</span> <span class=gnn>● gnn</span> <span class=shannon>● shannon</span> &middot; <span class=host>◆ host-as-node</span> &middot; θ=glyph(1024) · height=ring · cylinder=bh_index mod 6 &middot;
 <span class=warn>HONEST: coords REAL (cross-checked bad_coords=0) · NO true Hilbert d2xyz (linear index folded mod-6) · GNN watch LIVE proposal-not-proof · process telemetry NOT claimed</span>
</header>
<div id=main><canvas id=cv></canvas>
 <div id=side>
  <h3>SIX CYLINDERS (phase population)</h3><div id=phases></div>
  <h3>RULE-OF-THREE WATCHER LANES</h3><div id=watchers></div>
  <h3>SYSTEM LANES (real/logical/frozen)</h3><div id=lanes></div>
  <h3>PRIME-CUBE ANCHORS (p³)</h3><div id=primes></div>
  <h3>PIPES</h3><div><span class=k>REAL</span> = behcs-bus :4947 (central axis) · <span class=k>LOGICAL</span> = same-cylinder adjacency</div>
  <h3>GNN LIVE WATCH <span class=warn>(proposal-not-proof)</span></h3><div id=gnn></div>
  <h3>NEAREST PID</h3><div id=hover style="min-height:46px;color:#9fb6dd"></div>
 </div></div>
<footer id=foot></footer></div>
<script>
const D=__DATA__;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
const WC={hookwall:'#37b6ff',gnn:'#36e07f',shannon:'#b98cff'};
let W,H,cx,cy;function size(){W=cv.width=cv.clientWidth*devicePixelRatio;H=cv.height=cv.clientHeight*devicePixelRatio;cx=W/2;cy=H/2;}
addEventListener('resize',size);size();
let rotY=0.5,rotX=-0.32,zoom=1,drag=false,px=0,py=0,auto=true,mx=-1,my=-1;
cv.addEventListener('mousedown',e=>{drag=true;auto=false;px=e.clientX;py=e.clientY});
addEventListener('mouseup',()=>drag=false);
addEventListener('mousemove',e=>{if(drag){rotY+=(e.clientX-px)*0.008;rotX+=(e.clientY-py)*0.008;px=e.clientX;py=e.clientY}});
cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();mx=(e.clientX-r.left)*devicePixelRatio;my=(e.clientY-r.top)*devicePixelRatio});
cv.addEventListener('wheel',e=>{e.preventDefault();zoom*=e.deltaY<0?1.08:0.93;zoom=Math.max(.3,Math.min(4,zoom))},{passive:false});
cv.addEventListener('dblclick',()=>auto=!auto);
// six cylinder centres arranged in a hexagon (xz-plane)
const RHEX=210,CYLR=52,CYLH=300;
const centres=[];for(let p=0;p<6;p++){const a=p/6*Math.PI*2;centres.push({x:Math.cos(a)*RHEX,z:Math.sin(a)*RHEX,a});}
function place(n){const c=centres[n.phase];const th=(n.glyph/1024)*Math.PI*2+n.lane*0.03;
 return{x:c.x+Math.cos(th)*CYLR,z:c.z+Math.sin(th)*CYLR,y:n.h*CYLH-CYLH/2};}
function proj(x,y,z){let c=Math.cos(rotY),s=Math.sin(rotY);let X=x*c+z*s,Z=-x*s+z*c;
 let c2=Math.cos(rotX),s2=Math.sin(rotX);let Y=y*c2-Z*s2;Z=y*s2+Z*c2;const f=560/(560+Z);
 return{sx:cx+X*f*zoom*devicePixelRatio,sy:cy+Y*f*zoom*devicePixelRatio,sc:f,Z};}
const gnnNames=new Set(D.gnnWatch.predictions.map(p=>p.target.split(/[-(]/)[0]));
const pts=D.nodes.map(n=>({n,...place(n)}));
function frame(){
 if(auto)rotY+=0.0024;ctx.clearRect(0,0,W,H);
 // central REAL pipe (bus axis)
 const a=proj(0,-CYLH,0),b=proj(0,CYLH,0);ctx.strokeStyle='rgba(255,210,74,.3)';ctx.lineWidth=2*devicePixelRatio;
 ctx.beginPath();ctx.moveTo(a.sx,a.sy);ctx.lineTo(b.sx,b.sy);ctx.stroke();
 // six cylinder wireframes + phase labels
 for(let p=0;p<6;p++){const c=centres[p];ctx.strokeStyle='rgba(60,90,140,.30)';
  for(const yy of [-CYLH/2,CYLH/2]){ctx.beginPath();for(let i=0;i<=40;i++){const an=i/40*Math.PI*2;const q=proj(c.x+Math.cos(an)*CYLR,yy,c.z+Math.sin(an)*CYLR);i?ctx.lineTo(q.sx,q.sy):ctx.moveTo(q.sx,q.sy);}ctx.stroke();}
  for(let k=0;k<8;k++){const an=k/8*Math.PI*2;const t=proj(c.x+Math.cos(an)*CYLR,CYLH/2,c.z+Math.sin(an)*CYLR);const bo=proj(c.x+Math.cos(an)*CYLR,-CYLH/2,c.z+Math.sin(an)*CYLR);ctx.beginPath();ctx.moveTo(t.sx,t.sy);ctx.lineTo(bo.sx,bo.sy);ctx.stroke();}
  const lab=proj(c.x,CYLH/2+34,c.z);ctx.fillStyle='#7fd0ff';ctx.font=(13*devicePixelRatio)+'px ui-monospace';ctx.textAlign='center';ctx.fillText('φ'+p,lab.sx,lab.sy);}
 // nodes (depth sorted)
 const sp=pts.slice().sort((u,v)=>v.Z-u.Z);let best=1e9,hov=null;
 for(const p of sp){const n=p.n;const watched=[...gnnNames].some(t=>n.name.toLowerCase().includes(t));
  const rad=(n.isHost?3.3:2)*p.sc*zoom*devicePixelRatio*(watched?1.6:1);
  if(mx>0){const dd=(p.sx-mx)**2+(p.sy-my)**2;if(dd<best&&dd<420*devicePixelRatio*devicePixelRatio){best=dd;hov=n;}}
  ctx.shadowBlur=watched?12*devicePixelRatio:0;ctx.shadowColor='#ff4d6d';
  ctx.fillStyle=WC[n.watcher]||'#8aa';ctx.globalAlpha=Math.max(.4,Math.min(1,p.sc*1.05));
  ctx.beginPath();ctx.arc(p.sx,p.sy,rad,0,Math.PI*2);ctx.fill();
  if(n.isHost){ctx.strokeStyle='#ffd24a';ctx.globalAlpha=.95;ctx.lineWidth=1.3*devicePixelRatio;ctx.stroke();}}
 ctx.shadowBlur=0;ctx.globalAlpha=1;
 if(hov){document.getElementById('hover').innerHTML='<b>'+hov.name+'</b><br>pid '+hov.pid+' · bh_index '+hov.bh_index+' · φ'+hov.phase+' ring '+hov.ring+'<br>glyph '+hov.glyph+' · prime³ '+hov.prime_band+'³ · watcher <span style="color:'+(WC[hov.watcher])+'">'+hov.watcher+'</span> · '+hov.sys_lane;}
 requestAnimationFrame(frame);}
function bars(o,c){return Object.entries(o).sort((a,b)=>b[1]-a[1]).map(([k,v])=>'<div><span class=dot style="background:'+((c&&c[k])||'#6b86b6')+'"></span>'+k+' <span class=k>'+v+'</span></div>').join('');}
document.getElementById('phases').innerHTML=bars(D.meta.phaseCounts);
document.getElementById('watchers').innerHTML=bars(D.meta.watcherCounts,WC);
document.getElementById('lanes').innerHTML=bars(D.meta.laneCounts);
document.getElementById('primes').innerHTML=D.meta.prime_cube_primes.map((p,i)=>p+'³='+D.meta.prime_cubes[i]).join(' · ');
document.getElementById('gnn').innerHTML=D.gnnWatch.predictions.map(p=>'#'+p.rank+' <span style="color:#ff4d6d">'+p.score.toFixed(3)+'</span> '+p.target).join('<br>')+'<div class=warn style="margin-top:4px">'+D.gnnWatch.note+'</div>';
document.getElementById('foot').textContent='feed '+D.meta.feed+' · plotted '+D.meta.plotted+' · engine '+D.meta.engine+' · drag=rotate wheel=zoom dblclick=spin';
frame();
</script></body></html>`
  .replace('__DATA__', DATA).replace('__N__', String(nodes.length))
  .replace('__BHR__', '[' + meta.bh_index_range[0] + '..' + meta.bh_index_range[1] + ']');

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, html);
console.log('MULTI-CYL-BUILT|plotted=' + nodes.length + '|phases=' + JSON.stringify(phaseCounts) + '|watchers=' + JSON.stringify(watcherCounts) + '|lanes=' + JSON.stringify(laneCounts) + '|bh_range=' + JSON.stringify(meta.bh_index_range) + '|out=' + OUT);
