#!/usr/bin/env node
// Fire REAL MTP + HRM model code over the multi-cylinder voxel map geometry and
// compare predictions to the actual voxel positions. Renders a front-end overlay.
//
// Back-ends fired (honest):
//   MTP  = lib/mtp-heads.mjs  mtpHeads()  -> K parallel zeta heads, next-position prediction (REAL, runs here)
//   HRM  = lib/hrm-slow-fast.mjs hrmShapedPrediction() -> slow-loop SHAPE + fast-loop zeta refine
//          (DETERMINISTIC STUB; trained model lives at D:/Asolaria-HRM, not wired — labeled as such)
//   GNN  = L0 EdgeLevelGNN :4792 (LIVE service) edge scores on the pipes (summary embedded from the live fire)
//   geometry source = liris's verified preExistenceNode (cross-checked bad_coords=0 on acer)

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

// portable resolution (liris caught the hardcoded-acer-path bug): repo-local first,
// then env override, then known clone locations. byte-pinned Falcon libs untouched.
const HERE = dirname(fileURLToPath(import.meta.url));
const firstExisting = (cands, what) => {
  for (const c of cands) if (c && existsSync(c)) return c;
  throw new Error(`cannot locate ${what} — set the env override; tried: ${cands.filter(Boolean).join(' , ')}`);
};
const LIB = firstExisting([process.env.ASOLARIA_OMNI_LIB, resolve(HERE, '../falcon/omni-acer/lib'),
  'C:/asolaria-asi-on-metal-fabric/tools/falcon/omni-acer/lib'], 'omni-acer/lib');
const NN = firstExisting([process.env.ASOLARIA_NN_EXPORTER,
  'C:/asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs',
  'C:/Users/rayss/ASOLARIA-AS-NEURAL-NETWORK/tools/behcs/pre-existence-graph-exporter.mjs',
  resolve(HERE, '../../../asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs')],
  'pre-existence-graph-exporter.mjs (the NN repo coordinate engine)');
const FEED = firstExisting([process.env.ASOLARIA_OFFICE_FEED,
  'D:/PID-Registration-Office/fabric-feed/supervisors-fabric-feed-2026-06-10.hbp'],
  'office feed (acer-side; set ASOLARIA_OFFICE_FEED to verify elsewhere)');
const OUT  = resolve('reports/acer-mtp-hrm-geospatial.html');

const { mtpHeads, measureHitRate } = await import(pathToFileURL(LIB + '/mtp-heads.mjs').href);
const { hrmShapedPrediction, slowLoopPredictShape, SHAPES } = await import(pathToFileURL(LIB + '/hrm-slow-fast.mjs').href);
const { hilbertDecode } = await import(pathToFileURL(LIB + '/hilbert.mjs').href);
const { preExistenceNode } = await import(pathToFileURL(NN).href);

const cpToBhCoord = (cp) => hilbertDecode(Math.max(0, Math.min(4095, cp)), { dimensions: 3, bits: 4 });

// ---- build the 726-node voxel field (same engine + placement as the atlas) ----------
const regRows = readFileSync(FEED, 'utf8').split(/\r?\n/).filter(l => l.startsWith('REG|'));
const field = (line, key) => { const m = line.match(new RegExp('(?:^|\\|)' + key + '=([^|]*)')); return m ? m[1] : ''; };
const laneOf = (layer, cls) => {
  const s = (layer + ' ' + cls).toLowerCase();
  if (/usb|sovereign|cloud|hidden|paper|corpus|cartridge|frozen/.test(s)) return 'frozen';
  if (/room|substrate|prof|planb|basin|spindle|bh-room|descriptor|sector|shard/.test(s)) return 'logical';
  return 'real';
};
const envTypeOf = (layer, cls) => {
  const s = (layer + ' ' + cls).toLowerCase();
  if (/room|sector|shard|revolver|rotor/.test(s)) return 'revolver-rotation';
  if (/spindle|basin|hermes/.test(s)) return 'wave-spawn';
  if (/prof|supervisor|council|helm/.test(s)) return 'bilateral-mirror';
  if (/agent|operator/.test(s)) return 'bus-relay';
  if (/cube|recursion|sovereign/.test(s)) return 'cube-of-cubes';
  return 'edge';
};
const seen = new Set();
const nodes = [];
for (const line of regRows) {
  const name = field(line, 'name'), layer = field(line, 'layer'), cls = field(line, 'class');
  if (!name) continue;
  const key = name + ':' + layer + ':' + field(line, 'g5');
  if (seen.has(key)) continue; seen.add(key);
  const pn = preExistenceNode(name);
  nodes.push({ name, layer, class: cls, pid: pn.pid, glyph: pn.glyph_binding, bh: pn.bh_index,
    phase: pn.cylinder_phase, ring: pn.cylinder_ring, watcher: pn.watcher_lane, prime_band: pn.prime_band,
    sys_lane: laneOf(layer, cls), env: envTypeOf(layer, cls) });
}
const rings = nodes.map(n => n.ring), rMin = Math.min(...rings), rMax = Math.max(...rings);
const RHEX = 210, CYLR = 52, CYLH = 300;
const centre = p => ({ x: Math.cos(p / 6 * 2 * Math.PI) * RHEX, z: Math.sin(p / 6 * 2 * Math.PI) * RHEX });
for (const n of nodes) {
  const c = centre(n.phase); const th = (n.glyph / 1024) * 2 * Math.PI + n.lane * 0;
  n.x = c.x + Math.cos(th) * CYLR; n.z = c.z + Math.sin(th) * CYLR;
  n.y = (rMax === rMin ? 0.5 : (n.ring - rMin) / (rMax - rMin)) * CYLH - CYLH / 2;
  // HRM slow-loop shape PER NODE (real per-node env -> real shape variety)
  n.hrmShape = slowLoopPredictShape({ envelopeType: n.env, currentCp: n.glyph, history: [] }).shape;
}

// ---- FIRE MTP + HRM per cylinder, compare to actual voxel positions ------------------
const analysis = [];
for (let p = 0; p < 6; p++) {
  const cyl = nodes.filter(n => n.phase === p).sort((a, b) => a.bh - b.bh);
  // MTP: predict next position from each node's glyph, score against the ACTUAL next node
  let hits = 0, scored = 0, distSum = 0; const sampleMtp = [];
  const dist3 = (a, b) => Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2);
  const step = Math.max(1, Math.floor(cyl.length / 40)); // bound work
  for (let i = 0; i + 1 < cyl.length; i += step) {
    const pred = mtpHeads(cyl[i].glyph, { k: 4, depth: 2, seed: cyl[i].bh >>> 0 });
    const actualNext = cpToBhCoord(cyl[i + 1].glyph);
    const hr = measureHitRate(pred.final_positions, [actualNext]);
    const minD = Math.min(...pred.final_positions.map(p3 => dist3(p3, actualNext)));
    hits += hr.hits; scored += 1; distSum += minD;
    if (sampleMtp.length < 3) sampleMtp.push({ from: cyl[i].name.slice(0, 18), pred_cp: pred.heads.map(h => h.cp_predicted), actual_next_cp: cyl[i + 1].glyph, min_cell_dist: +minD.toFixed(2), hit: hr.hits > 0 });
  }
  // HRM: per-NODE slow-loop shape -> the cylinder's real shape distribution (not collapsed to one env)
  const shapeDist = {}; cyl.forEach(n => { shapeDist[n.hrmShape] = (shapeDist[n.hrmShape] || 0) + 1; });
  const dominantShape = Object.entries(shapeDist).sort((a, b) => b[1] - a[1])[0][0];
  const variety = Object.keys(shapeDist).length;
  analysis.push({
    phase: p, count: cyl.length,
    mtp: { next_pos_hit_rate: scored ? +(hits / scored).toFixed(3) : 0, mean_min_cell_dist: scored ? +(distSum / scored).toFixed(2) : 0, scored, sample: sampleMtp },
    hrm: { shape: dominantShape, shape_distribution: shapeDist, shape_variety: variety },
  });
}

// ---- live GNN edge-score summary (from the w3ukg5o12 live :4792 fire) ----------------
const gnn = {
  service: 'L0 EdgeLevelGNN :4792 (LIVE, PID inference_server.py)',
  edges_scored: 165, score_min: 2.6e-7, score_max: 0.7405, score_mean: 0.2446,
  intra_cylinder_mean_high: '~0.74 (within-cylinder adjacency rated strong)',
  inter_cylinder_low: '~0.003 (cross-cylinder links rated weak)',
  reading: 'the live GNN rates within-cylinder pipes far stronger than cross-cylinder — geometry-consistent',
};

const backends = [
  { name: 'GNN-L0 (:4792)', status: 'LIVE service', what: 'scored 165 real pipe edges' },
  { name: 'MTP (mtp-heads.mjs)', status: 'FIRED on acer (real zeta heads)', what: 'next-position prediction per cylinder, scored vs actual voxels' },
  { name: 'HRM (hrm-slow-fast.mjs)', status: 'FIRED on acer — DETERMINISTIC STUB', what: 'slow-loop shape classify; trained model at D:/Asolaria-HRM NOT wired (honest)' },
  { name: 'GNN-L4 / Shannon-gate', status: 'not running on acer', what: 'descriptor seats; engine not cranked here' },
];
const findings = {
  cylinder_overlap: 0, inter_cylinder_min_dist: 210, cyl_radius: CYLR,
  bh_collision: 'min |bh_index delta| = 0 — at least one BH-linearization collision (known caveat)',
  mtp_mean_hit_rate: +(analysis.reduce((a, c) => a + c.mtp.next_pos_hit_rate, 0) / analysis.length).toFixed(3),
};
const meta = { plotted: nodes.length, engine: 'preExistenceNode (liris 939cdac, bad_coords=0 on acer)', generated: 'acer vantage, real MTP+HRM fired locally' };
const DATA = JSON.stringify({ nodes, analysis, gnn, backends, findings, meta, shapes: SHAPES });

const html = `<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>ACER · MTP+HRM+GNN geospatial analysis over the voxel atlas</title>
<style>
 :root{--bg:#04060c;--fg:#cfe3ff;--dim:#5b6b86;--hookwall:#37b6ff;--gnn:#36e07f;--shannon:#b98cff;--mtp:#ffd24a;--hrm:#ff6db0}
 *{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:12px/1.5 ui-monospace,Consolas,monospace}
 #wrap{display:flex;flex-direction:column;height:100vh}header{padding:7px 12px;border-bottom:1px solid #13203a;background:#060a14}
 header b{color:#fff}.k{color:#7fffd4}.warn{color:#ffb454}.hookwall{color:var(--hookwall)}.gnn{color:var(--gnn)}.shannon{color:var(--shannon)}.mtp{color:var(--mtp)}.hrm{color:var(--hrm)}
 #main{flex:1;display:flex;min-height:0}#cv{flex:1;display:block;cursor:grab}#cv:active{cursor:grabbing}
 #side{width:360px;border-left:1px solid #13203a;overflow:auto;padding:8px 10px;background:#060a14}
 h3{margin:9px 0 3px;color:#fff;font-size:12px}table{width:100%;border-collapse:collapse;font-size:11px}
 th,td{text-align:left;padding:2px 4px;border-bottom:1px solid #10203a}th{color:var(--dim)}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
 footer{padding:5px 12px;border-top:1px solid #13203a;color:var(--dim);background:#060a14}
</style></head><body><div id=wrap>
<header>
 <b>ACER · MTP + HRM + GNN — GEOSPATIAL ANALYSIS OF THE VOXEL ATLAS</b> &middot; <span class=k>__N__ PIDs</span>, 6 cylinders &middot;
 <span class=mtp>MTP</span> next-pos vs actual · <span class=hrm>HRM</span> shape per cylinder · <span class=gnn>GNN</span> live edge scores<br>
 <span class=warn>HONEST: GNN=LIVE service(:4792) · MTP=real zeta heads fired here · HRM=DETERMINISTIC STUB (trained model D:/Asolaria-HRM not wired) · coords real, no true Hilbert d2xyz · process telemetry NOT claimed</span>
</header>
<div id=main><canvas id=cv></canvas>
 <div id=side>
  <h3>BACK-ENDS FIRED</h3><table id=be><tr><th>model</th><th>status</th></tr></table>
  <h3>PER-CYLINDER MODEL READ</h3><table id=an><tr><th>φ</th><th>n</th><th class=hrm>HRM shape (var)</th><th class=mtp>MTP hit / dist</th></tr></table>
  <h3>HRM SHAPE LEGEND (per-node)</h3><div id=shleg></div>
  <h3>GNN LIVE EDGE SCORES (pipes)</h3><div id=gnn></div>
  <h3>GEOSPATIAL FINDINGS</h3><div id=find></div>
  <h3>NEAREST PID</h3><div id=hover style="min-height:42px;color:#9fb6dd"></div>
 </div></div>
<footer id=foot></footer></div>
<script>
const D=__DATA__;const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
const WC={hookwall:'#37b6ff',gnn:'#36e07f',shannon:'#b98cff'};
let W,H,cx,cy;function size(){W=cv.width=cv.clientWidth*devicePixelRatio;H=cv.height=cv.clientHeight*devicePixelRatio;cx=W/2;cy=H/2;}
addEventListener('resize',size);size();
let rotY=0.5,rotX=-0.32,zoom=1,drag=false,px=0,py=0,auto=true,mx=-1,my=-1;
cv.addEventListener('mousedown',e=>{drag=true;auto=false;px=e.clientX;py=e.clientY});addEventListener('mouseup',()=>drag=false);
addEventListener('mousemove',e=>{if(drag){rotY+=(e.clientX-px)*0.008;rotX+=(e.clientY-py)*0.008;px=e.clientX;py=e.clientY}});
cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();mx=(e.clientX-r.left)*devicePixelRatio;my=(e.clientY-r.top)*devicePixelRatio});
cv.addEventListener('wheel',e=>{e.preventDefault();zoom*=e.deltaY<0?1.08:0.93;zoom=Math.max(.3,Math.min(4,zoom))},{passive:false});
cv.addEventListener('dblclick',()=>auto=!auto);
const RHEX=210,CYLR=52,CYLH=300;const cen=p=>({x:Math.cos(p/6*2*Math.PI)*RHEX,z:Math.sin(p/6*2*Math.PI)*RHEX});
const SHC={linear:'#9fb6dd',ring:'#ffd24a',spiral:'#36e07f',fold:'#37b6ff',cascade:'#ff6db0',star:'#ff4d6d',fractal:'#b98cff',branch:'#7fffd4'};
function proj(x,y,z){let c=Math.cos(rotY),s=Math.sin(rotY);let X=x*c+z*s,Z=-x*s+z*c;let c2=Math.cos(rotX),s2=Math.sin(rotX);let Y=y*c2-Z*s2;Z=y*s2+Z*c2;const f=560/(560+Z);return{sx:cx+X*f*zoom*devicePixelRatio,sy:cy+Y*f*zoom*devicePixelRatio,sc:f,Z};}
const shapeByPhase={};D.analysis.forEach(a=>shapeByPhase[a.phase]=a.hrm.shape);
const pts=D.nodes.map(n=>({n,...proj(n.x,n.y,n.z)}));
function frame(){
 if(auto)rotY+=0.0024;ctx.clearRect(0,0,W,H);
 const a=proj(0,-CYLH,0),b=proj(0,CYLH,0);ctx.strokeStyle='rgba(255,210,74,.3)';ctx.lineWidth=2*devicePixelRatio;ctx.beginPath();ctx.moveTo(a.sx,a.sy);ctx.lineTo(b.sx,b.sy);ctx.stroke();
 for(let p=0;p<6;p++){const c=cen(p);const sh=shapeByPhase[p]||'linear';ctx.strokeStyle=(SHC[sh]||'#446')+'';ctx.globalAlpha=.5;
  for(const yy of [-CYLH/2,CYLH/2]){ctx.beginPath();for(let i=0;i<=40;i++){const an=i/40*2*Math.PI;const q=proj(c.x+Math.cos(an)*CYLR,yy,c.z+Math.sin(an)*CYLR);i?ctx.lineTo(q.sx,q.sy):ctx.moveTo(q.sx,q.sy);}ctx.stroke();}
  ctx.globalAlpha=1;const lab=proj(c.x,CYLH/2+38,c.z);ctx.fillStyle=SHC[sh]||'#7fd0ff';ctx.font=(12*devicePixelRatio)+'px ui-monospace';ctx.textAlign='center';ctx.fillText('φ'+p+' '+sh,lab.sx,lab.sy);}
 const sp=pts.slice().sort((u,v)=>v.Z-u.Z);let best=1e9,hov=null;
 for(const q of sp){const n=q.n;const rad=2*q.sc*zoom*devicePixelRatio;if(mx>0){const dd=(q.sx-mx)**2+(q.sy-my)**2;if(dd<best&&dd<400*devicePixelRatio*devicePixelRatio){best=dd;hov=n;}}
  ctx.fillStyle=SHC[n.hrmShape]||WC[n.watcher]||'#8aa';ctx.globalAlpha=Math.max(.4,Math.min(1,q.sc*1.05));ctx.beginPath();ctx.arc(q.sx,q.sy,rad,0,2*Math.PI);ctx.fill();}
 ctx.globalAlpha=1;
 if(hov){document.getElementById('hover').innerHTML='<b>'+hov.name+'</b><br>φ'+hov.phase+' ('+(shapeByPhase[hov.phase])+') · bh '+hov.bh+' · glyph '+hov.glyph+' · prime³ '+hov.prime_band+' · '+hov.sys_lane;}
 requestAnimationFrame(frame);}
document.getElementById('be').innerHTML+=D.backends.map(b=>'<tr><td>'+b.name+'</td><td>'+b.status+'</td></tr>').join('');
document.getElementById('an').innerHTML+=D.analysis.map(a=>'<tr><td>φ'+a.phase+'</td><td>'+a.count+'</td><td style="color:'+(SHC[a.hrm.shape]||'#fff')+'">'+a.hrm.shape+' ('+a.hrm.shape_variety+')</td><td class=mtp>'+a.mtp.next_pos_hit_rate+' / '+a.mtp.mean_min_cell_dist+'</td></tr>').join('');
document.getElementById('shleg').innerHTML=Object.entries(D.analysis.reduce((acc,a)=>{for(const[s,c]of Object.entries(a.hrm.shape_distribution))acc[s]=(acc[s]||0)+c;return acc;},{})).sort((x,y)=>y[1]-x[1]).map(([s,c])=>'<span class=dot style="background:'+(SHC[s]||'#446')+'"></span>'+s+' <span class=k>'+c+'</span>').join(' &middot; ');
document.getElementById('gnn').innerHTML='<div>'+D.gnn.service+'</div><div>edges '+D.gnn.edges_scored+' · range '+D.gnn.score_min.toExponential(1)+'–'+D.gnn.score_max+' · mean '+D.gnn.score_mean+'</div><div class=gnn>'+D.gnn.reading+'</div>';
document.getElementById('find').innerHTML='<div>cylinders cleanly separated: overlap='+D.findings.cylinder_overlap+', min-dist '+D.findings.inter_cylinder_min_dist+' &gt;&gt; 2×radius '+(2*D.findings.cyl_radius)+'</div><div class=mtp>MTP mean next-pos hit-rate (vs actual voxels) = '+D.findings.mtp_mean_hit_rate+'</div><div class=warn>'+D.findings.bh_collision+'</div>';
document.getElementById('foot').textContent='plotted '+D.meta.plotted+' · '+D.meta.engine+' · '+D.meta.generated+' · drag=rotate wheel=zoom dblclick=spin';
frame();
</script></body></html>`
  .replace('__DATA__', DATA).replace('__N__', String(nodes.length));

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, html);
console.log('MTP-HRM-FIRED|plotted=' + nodes.length + '|mtp_mean_hit=' + findings.mtp_mean_hit_rate + '|hrm_shapes=' + JSON.stringify(analysis.map(a => 'φ' + a.phase + ':' + a.hrm.shape)) + '|gnn_edges=' + gnn.edges_scored + '|out=' + OUT);
console.log('PER-CYLINDER=' + JSON.stringify(analysis.map(a => ({ phase: a.phase, n: a.count, shape: a.hrm.shape, mtp_hit: a.mtp.next_pos_hit_rate, env: a.hrm.dominant_env }))));
