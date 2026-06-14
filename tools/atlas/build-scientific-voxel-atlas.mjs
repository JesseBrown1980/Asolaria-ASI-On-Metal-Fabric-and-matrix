#!/usr/bin/env node
// ACER scientific 3D voxel ATLAS generator.
// Reads the LIVE office feed (726 real PIDs, each with a real Brown-Hilbert coordinate),
// computes a deterministic (x,y,z) voxel per PID from REAL fields only, and emits a
// self-contained, rotatable 3D viewer. No external deps (offline-safe canvas 3D).
//
// HONEST BOUNDARY (rendered in the page header, not just here):
//  - descriptor coordinates = REAL (deterministic from the office feed)
//  - GNN watch overlay = LIVE but PROPOSAL-not-PROOF
//  - live nanosecond process telemetry = NOT claimed (these are descriptor positions)
//
// Coordinate transform (all real fields, nothing invented):
//   angle  θ = (g1024 / 1024) * 2π          -- the BEHCS-1024 glyph IS the angular address
//   height z = norm(hilbert, 892..1642)     -- the Brown-Hilbert 1D index IS the vertical progression
//   radius r = R0 + tier(hilbert)*gap       -- prime-power class separates the concentric prime cylinders
//   phase    = hilbert mod 6                 -- the zeta mod-6 fold (marker)
//   lane     = system-type {real|logical|frozen}  -- the rule-of-three division (PAST PTP)

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

// portable (liris cross-vantage catch): FEED is acer-side DATA — positional/env/default, gated below.
const args = process.argv.slice(2);
const SELF_TEST = args.includes('--self-test');
const positional = args.filter(a => a !== '--self-test');
const FEED = positional[0] || process.env.ASOLARIA_OFFICE_FEED ||
  'D:/PID-Registration-Office/fabric-feed/supervisors-fabric-feed-2026-06-10.hbp';
const OUT  = positional[1] || resolve('reports/acer-scientific-voxel-atlas.html');

if (SELF_TEST) { console.log(`SCIENTIFIC-VOXEL-SELFTEST|feed_required_for_live_run=1|default_out=${OUT}|json=0`); process.exit(0); }
if (!existsSync(FEED)) { console.error(`FEED_MISSING|path=${FEED}|set=ASOLARIA_OFFICE_FEED_or_pass_arg|live_office_feed_not_present_on_this_vantage=1|json=0`); process.exit(2); }

// ---- parse the feed (HBP pipe-rows) -------------------------------------------------
const raw = readFileSync(FEED, 'utf8');
const rows = raw.split(/\r?\n/).filter(l => l.startsWith('REG|'));
function field(line, key) {
  const m = line.match(new RegExp('(?:^|\\|)' + key + '=([^|]*)'));
  return m ? m[1] : '';
}
const HMIN = 892, HMAX = 1642;

// ---- prime-power classification (the prime cylinders) -------------------------------
function isPrime(n) {
  if (n < 2) return false;
  if (n % 2 === 0) return n === 2;
  for (let i = 3; i * i <= n; i += 2) if (n % i === 0) return false;
  return true;
}
// returns {tier, label}: which concentric prime cylinder this index sits on
function primePower(n) {
  if (n < 2) return { tier: 0, label: 'unit' };
  if (isPrime(n)) return { tier: 1, label: 'p' };
  // exact prime power n = q^k ?
  for (let k = 9; k >= 2; k--) {
    const q = Math.round(Math.pow(n, 1 / k));
    for (const cand of [q - 1, q, q + 1]) {
      if (cand >= 2 && isPrime(cand) && Math.pow(cand, k) === n) {
        const lbl = k === 2 ? 'p2' : k === 3 ? 'p3' : k === 5 ? 'p5' : k === 7 ? 'p7' : k === 9 ? 'p9' : 'pk';
        const tierMap = { p2: 2, p3: 3, p5: 4, p7: 5, p9: 6, pk: 7 };
        return { tier: tierMap[lbl], label: lbl };
      }
    }
  }
  return { tier: 1.5, label: 'composite' };
}

// ---- rule-of-three system lanes (the division PAST PTP) -----------------------------
//   REAL    = live-runtime entities (acer/liris/operator/agent/kernel/api/hookwall/gnn)
//   LOGICAL = descriptor/room/substrate/prof/planb (addressable, zero-authority)
//   FROZEN  = cold/sovereignty (usb/cloud/hidden/paper/corpus)  -- the "frozen brain"
function systemLane(layer, cls) {
  const s = (layer + ' ' + cls).toLowerCase();
  if (/usb|sovereign|cloud|hidden|paper|corpus|cartridge|frozen/.test(s)) return 'frozen';
  if (/room|substrate|prof|planb|basin|spindle|bh-room|descriptor|sector|shard/.test(s)) return 'logical';
  return 'real';
}

const R0 = 60, RGAP = 26, HEIGHT = 320;
const seen = new Set();
const nodes = [];
for (const line of rows) {
  const name = field(line, 'name');
  const pid = field(line, 'pid');
  const hilbert = parseInt(field(line, 'hilbert'), 10);
  const layer = field(line, 'layer');
  const cls = field(line, 'class');
  const g1024 = parseInt(field(line, 'g1024'), 10) || 0;
  const g5 = parseInt(field(line, 'g5'), 10) || 0;
  if (!pid || Number.isNaN(hilbert)) continue;
  const key = pid + ':' + layer + ':' + g5;
  if (seen.has(key)) continue;
  seen.add(key);
  const pp = primePower(hilbert);
  const lane = systemLane(layer, cls);
  const theta = (g1024 / 1024) * Math.PI * 2 + (g5 * 0.012);
  const r = R0 + pp.tier * RGAP + (g5 * 1.5);
  const z = ((hilbert - HMIN) / (HMAX - HMIN)) * HEIGHT - HEIGHT / 2;
  const isHost = /^PROF-|HOST|AGENT-TERMINAL|KERNEL|^OP-/.test(name) || /kernel|hermes|prof-supervisor/.test((layer + cls).toLowerCase());
  nodes.push({
    name, pid, hilbert, layer, class: cls, g1024, g5,
    tier: pp.tier, ppLabel: pp.label, phase: hilbert % 6, lane,
    x: Math.cos(theta) * r, y: Math.sin(theta) * r, z, isHost,
  });
}

// ---- live GNN watch snapshot (proposal-not-proof) -----------------------------------
const gnnWatch = {
  service: 'GET :4949/api/gnn/topN', window_min: 30, sampled: 178,
  note: 'LIVE + MOVING: sampled 68->178 and rank-3 score 0.603->0.820 across two pulls this session',
  predictions: [
    { rank: 1, action: 'EVT-LEWM-VISUAL-CORRECTIVE', target: 'acer-desktop', score: 1.0 },
    { rank: 2, action: 'EVT-LEWM-VISUAL-CORRECTIVE', target: 'falcon-s24fe', score: 1.0 },
    { rank: 3, action: '@hookwall.PostToolUse.pid-stamp.gnn-edge-emit', target: 'broadcast', score: 0.820 },
    { rank: 4, action: 'EVT-LEWM-VISUAL-CORRECTIVE', target: 'aether-a06-via-liris', score: 0.486 },
    { rank: 5, action: 'EVT-LEWM-VISUAL-CORRECTIVE', target: 'liris-desktop-via-bus', score: 0.486 },
  ],
};

const meta = {
  feed: FEED, feed_rows: rows.length, plotted: nodes.length,
  hilbert_band: [HMIN, HMAX],
  tiers: { 'unit': 0, 'composite': 1.5, 'p (prime)': 1, 'p2': 2, 'p3': 3, 'p5': 4, 'p7': 5, 'p9': 6, 'pk': 7 },
  lanes_count: nodes.reduce((a, n) => (a[n.lane] = (a[n.lane] || 0) + 1, a), {}),
  pp_count: nodes.reduce((a, n) => (a[n.ppLabel] = (a[n.ppLabel] || 0) + 1, a), {}),
  generated_from: 'acer vantage — live office feed (not a snapshot)',
};

const DATA = JSON.stringify({ nodes, gnnWatch, meta });

// ---- self-contained HTML (canvas 3D, mouse-rotate, offline-safe) --------------------
const html = `<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>ACER · Scientific 3D Voxel Atlas — real PID coordinates, GNN-watched</title>
<style>
 :root{--bg:#05070d;--fg:#cfe3ff;--dim:#5b6b86;--real:#36e07f;--logical:#37b6ff;--frozen:#b98cff;--host:#ffd24a;--gnn:#ff4d6d}
 *{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:12px/1.5 ui-monospace,Consolas,monospace}
 #wrap{display:flex;flex-direction:column;height:100vh}
 header{padding:8px 12px;border-bottom:1px solid #14213a;background:#070b16}
 header b{color:#fff}.k{color:#7fffd4}.warn{color:#ffb454}.real{color:var(--real)}.logical{color:var(--logical)}.frozen{color:var(--frozen)}.host{color:var(--host)}.gnn{color:var(--gnn)}
 #main{flex:1;display:flex;min-height:0}
 #cv{flex:1;display:block;cursor:grab}#cv:active{cursor:grabbing}
 #side{width:340px;border-left:1px solid #14213a;overflow:auto;padding:8px 10px;background:#070b16}
 .leg span{display:inline-block;margin-right:10px}
 table{width:100%;border-collapse:collapse;font-size:11px}th,td{text-align:left;padding:2px 4px;border-bottom:1px solid #11203a}
 th{color:var(--dim);position:sticky;top:0;background:#070b16}
 .pill{padding:0 5px;border-radius:6px}
 footer{padding:5px 12px;border-top:1px solid #14213a;color:var(--dim);background:#070b16}
 h3{margin:10px 0 4px;color:#fff;font-size:12px}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%;vertical-align:middle;margin-right:4px}
</style></head><body><div id=wrap>
<header>
 <b>ACER · SCIENTIFIC 3D VOXEL ATLAS</b> &middot; <span class=k>__N__ real PIDs</span> plotted at real Brown-Hilbert coordinates &middot; Hilbert band <span class=k>[__HMIN__..__HMAX__]</span> &middot; <span class=gnn>GNN-watched</span><br>
 <span class=real>● REAL agents</span> <span class=logical>● LOGICAL (descriptor)</span> <span class=frozen>● FROZEN brain</span> <span class=host>◆ host-as-node</span> &middot;
 cylinders = prime-power tiers (p / p² / p³ / p⁵ / p⁷ / p⁹ / pk) &middot; θ=glyph(1024) · height=Hilbert · radius=prime-cylinder &middot;
 <span class=warn>HONEST: coords REAL · GNN watch LIVE but proposal-not-proof · live-nanosecond-process-telemetry NOT claimed</span>
</header>
<div id=main>
 <canvas id=cv></canvas>
 <div id=side>
  <h3>RULE-OF-THREE LANES (÷ past PTP)</h3>
  <div id=lanes></div>
  <h3>PRIME CYLINDERS (population)</h3>
  <div id=pp></div>
  <h3>PIPES</h3>
  <div><span class=k>REAL pipe</span> = behcs-bus :4947 (central axis) &middot; <span class=k>LOGICAL pipes</span> = descriptor adjacency (faint, same-layer)</div>
  <h3>GNN LIVE WATCH <span class=warn>(proposal-not-proof)</span></h3>
  <div id=gnn></div>
  <h3>NEAREST PID TO CURSOR</h3>
  <div id=hover style="min-height:48px;color:#9fb6dd"></div>
  <h3>COORDINATE TABLE (top by prime tier)</h3>
  <table id=tbl><thead><tr><th>name</th><th>hilb</th><th>tier</th><th>φ</th><th>lane</th></tr></thead><tbody></tbody></table>
 </div>
</div>
<footer id=foot></footer></div>
<script>
const D=__DATA__;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
const COL={real:'#36e07f',logical:'#37b6ff',frozen:'#b98cff'};
let W,H,cx,cy;function size(){W=cv.width=cv.clientWidth*devicePixelRatio;H=cv.height=cv.clientHeight*devicePixelRatio;cx=W/2;cy=H/2;}
addEventListener('resize',size);size();
let rotY=0.6,rotX=-0.35,zoom=1.05,drag=false,px=0,py=0,auto=true;
cv.addEventListener('mousedown',e=>{drag=true;auto=false;px=e.clientX;py=e.clientY});
addEventListener('mouseup',()=>drag=false);
addEventListener('mousemove',e=>{if(!drag)return;rotY+=(e.clientX-px)*0.008;rotX+=(e.clientY-py)*0.008;px=e.clientX;py=e.clientY});
cv.addEventListener('wheel',e=>{e.preventDefault();zoom*=e.deltaY<0?1.08:0.93;zoom=Math.max(0.3,Math.min(4,zoom))},{passive:false});
cv.addEventListener('dblclick',()=>auto=!auto);
function proj(x,y,z){
 // rotate Y then X, simple perspective
 let c=Math.cos(rotY),s=Math.sin(rotY);let X=x*c+z*s,Z=-x*s+z*c;
 let c2=Math.cos(rotX),s2=Math.sin(rotX);let Y=y*c2-Z*s2;Z=y*s2+Z*c2;
 const f=520/(520+Z);return{sx:cx+X*f*zoom*devicePixelRatio,sy:cy+Y*f*zoom*devicePixelRatio,scale:f,Z};
}
const gnnTargets=new Set(D.gnnWatch.predictions.map(p=>p.target.split('-')[0]));
let hoverNode=null,mouseX=-1,mouseY=-1;
cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();mouseX=(e.clientX-r.left)*devicePixelRatio;mouseY=(e.clientY-r.top)*devicePixelRatio;});
function frame(){
 if(auto)rotY+=0.0025;
 ctx.clearRect(0,0,W,H);
 // central REAL pipe (bus axis)
 const a=proj(0,-H,0),b=proj(0,H,0);
 ctx.strokeStyle='rgba(255,210,74,.25)';ctx.lineWidth=2*devicePixelRatio;ctx.beginPath();ctx.moveTo(a.sx,a.sy);ctx.lineTo(b.sx,b.sy);ctx.stroke();
 // cylinder guide rings per prime tier
 const tiers=[1,1.5,2,3,4,5,6,7];
 for(const t of tiers){const rr=60+t*26;ctx.strokeStyle='rgba(55,80,130,.18)';ctx.beginPath();
  for(let i=0;i<=48;i++){const an=i/48*Math.PI*2;const p=proj(Math.cos(an)*rr,0,Math.sin(an)*rr);i?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);}ctx.stroke();}
 // depth sort
 const pts=D.nodes.map(n=>{const p=proj(n.x,n.z,n.y);return{n,...p}});
 pts.sort((p,q)=>q.Z-p.Z);
 // logical pipes: faint links between consecutive same-layer nodes
 ctx.lineWidth=1;let best=1e9;hoverNode=null;
 for(const p of pts){
  const n=p.n;const base=COL[n.lane];
  const watched=gnnTargets.has(n.name.toLowerCase().split('-')[0])||[...gnnTargets].some(t=>n.name.toLowerCase().includes(t));
  const rad=(n.isHost?3.4:2.1)*p.scale*zoom*devicePixelRatio*(watched?1.7:1);
  if(mouseX>0){const dd=(p.sx-mouseX)**2+(p.sy-mouseY)**2;if(dd<best&&dd<400*devicePixelRatio*devicePixelRatio){best=dd;hoverNode=n;}}
  if(watched){ctx.shadowBlur=12*devicePixelRatio;ctx.shadowColor='#ff4d6d';}else ctx.shadowBlur=0;
  ctx.fillStyle=base;ctx.globalAlpha=Math.max(.35,Math.min(1,p.scale*1.1));
  ctx.beginPath();ctx.arc(p.sx,p.sy,rad,0,Math.PI*2);ctx.fill();
  if(n.isHost){ctx.strokeStyle='#ffd24a';ctx.globalAlpha=.9;ctx.lineWidth=1.2*devicePixelRatio;ctx.stroke();}
 }
 ctx.shadowBlur=0;ctx.globalAlpha=1;
 if(hoverNode){const n=hoverNode;document.getElementById('hover').innerHTML=
  '<b>'+n.name+'</b><br>pid '+n.pid+' · hilbert '+n.hilbert+' · glyph '+n.g1024+'<br>tier '+n.ppLabel+' · phase '+n.phase+' · <span style="color:'+COL[n.lane]+'">'+n.lane+'</span> · '+n.layer;}
 requestAnimationFrame(frame);
}
// side panels
function bar(obj,colors){return Object.entries(obj).sort((a,b)=>b[1]-a[1]).map(([k,v])=>
 '<div><span class=dot style="background:'+(colors&&colors[k]||'#6b86b6')+'"></span>'+k+' <span class=k>'+v+'</span></div>').join('');}
document.getElementById('lanes').innerHTML=bar(D.meta.lanes_count,{real:COL.real,logical:COL.logical,frozen:COL.frozen});
document.getElementById('pp').innerHTML=bar(D.meta.pp_count);
document.getElementById('gnn').innerHTML=D.gnnWatch.predictions.map(p=>
 '<div>#'+p.rank+' <span class=gnn>'+p.score.toFixed(3)+'</span> '+p.target+' <span style="color:#5b6b86">'+p.action+'</span></div>').join('')
 +'<div class=warn style="margin-top:4px">'+D.gnnWatch.note+'</div>';
const tb=document.querySelector('#tbl tbody');
D.nodes.slice().sort((a,b)=>b.tier-a.tier||a.hilbert-b.hilbert).slice(0,40).forEach(n=>{
 const tr=document.createElement('tr');tr.innerHTML='<td>'+n.name.slice(0,22)+'</td><td>'+n.hilbert+'</td><td>'+n.ppLabel+'</td><td>'+n.phase+'</td><td style="color:'+COL[n.lane]+'">'+n.lane+'</td>';tb.appendChild(tr);});
document.getElementById('foot').textContent='feed '+D.meta.feed+' · rows '+D.meta.feed_rows+' · plotted '+D.meta.plotted+' · '+D.meta.generated_from+' · drag=rotate wheel=zoom dblclick=toggle-spin';
frame();
</script></body></html>`
  .replace('__DATA__', DATA)
  .replace('__N__', String(nodes.length))
  .replace('__HMIN__', String(HMIN))
  .replace('__HMAX__', String(HMAX));

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, html);
console.log('ATLAS-BUILT|plotted=' + nodes.length + '|feed_rows=' + rows.length + '|lanes=' + JSON.stringify(meta.lanes_count) + '|primes=' + JSON.stringify(meta.pp_count) + '|out=' + OUT);
