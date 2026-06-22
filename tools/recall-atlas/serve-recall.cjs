const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const https = require('https');
const path = require('path');
const url = require('url');

const PORT = Number(process.env.PORT || 4791);
const BIND = process.env.ASOLARIA_RECALL_BIND || '127.0.0.1';
const COLONY = process.env.ASOLARIA_RECALL_COLONY || 'liris';
const OWNER_PID = process.env.ASOLARIA_RECALL_OWNER_PID || 'OP-RAYSSA-PID';
const DIR = process.env.ASOLARIA_RECALL_DIR || 'C:/tmp/asolaria-unified-archaeology';
const HBP = path.join(DIR, 'ASOLARIA-LIRIS-RECALL.hbp');
const HBI = path.join(DIR, 'ASOLARIA-LIRIS-RECALL.hbi');
const SUMMARY = path.join(DIR, 'SUMMARY-LIRIS.json');
const KEY_FILE = process.env.ASOLARIA_RECALL_KEY_FILE
  || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.asolaria', 'recall.key');
const SHARED_KEY = loadSecret();
const PEERS = parsePeers(process.env.ASOLARIA_RECALL_PEERS || '');
const ALLOWED_OWNER_PIDS = parseCsv(process.env.ASOLARIA_RECALL_ALLOWED_OWNER_PIDS || 'OP-JESSE-PID,OP-RAYSSA-PID');

function parseCsv(raw) {
  return String(raw || '').split(',').map(x => x.trim()).filter(Boolean);
}

function loadSecret() {
  const envKey = String(process.env.ASOLARIA_RECALL_KEY || '').trim();
  if (envKey) return envKey;
  try {
    const key = fs.readFileSync(KEY_FILE, 'utf8').trim();
    return key || '';
  } catch {
    return '';
  }
}

function parsePeers(raw) {
  return String(raw || '')
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
    .map((part, i) => {
      const eq = part.indexOf('=');
      if (eq > 0) {
        return { name: part.slice(0, eq).trim(), base: part.slice(eq + 1).trim().replace(/\/+$/, '') };
      }
      return { name: `peer${i + 1}`, base: part.replace(/\/+$/, '') };
    })
    .filter(peer => /^https?:\/\//i.test(peer.base));
}

function readSummary() {
  try { return JSON.parse(fs.readFileSync(SUMMARY, 'utf8')); } catch { return { ok: false, error: 'summary missing' }; }
}

function parseParts(line) {
  const out = {};
  for (const part of line.split('|').slice(1)) {
    const i = part.indexOf('=');
    if (i > -1) out[part.slice(0, i)] = part.slice(i + 1);
  }
  return out;
}

function safeLowerPath(value) {
  const raw = String(value || '');
  try { return decodeURIComponent(raw).toLowerCase(); } catch { return raw.toLowerCase(); }
}

function readIndex() {
  if (!fs.existsSync(HBI)) return [];
  return fs.readFileSync(HBI, 'utf8').split(/\r?\n/).filter(line => line.startsWith('IDX|')).map(parseParts);
}

const index = readIndex();

function seekRow(entry) {
  if (!entry) return null;
  const fd = fs.openSync(HBP, 'r');
  try {
    const buf = Buffer.alloc(Number(entry.len));
    fs.readSync(fd, buf, 0, buf.length, Number(entry.off));
    return buf.toString('utf8').trimEnd();
  } finally {
    fs.closeSync(fd);
  }
}

function searchLocal(rawQuery, rawLimit) {
  const q = String(rawQuery || '').toLowerCase();
  const limit = Math.max(1, Math.min(250, Number(rawLimit || 50)));
  const matches = [];
  for (const e of index) {
    if (matches.length >= limit) break;
    if (!q || e.pid.includes(q) || e.bh.includes(q) || safeLowerPath(e.path).includes(q)) {
      matches.push({ index: e, row: seekRow(e) });
    }
  }
  return { q, count: matches.length, matches };
}

function json(res, obj, status = 200) {
  const body = JSON.stringify(obj, null, 2);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
  });
  res.end(body);
}

function isLoopback(remoteAddress) {
  return remoteAddress === '127.0.0.1'
    || remoteAddress === '::1'
    || remoteAddress === '::ffff:127.0.0.1';
}

function suppliedKey(req) {
  const direct = req.headers['x-asolaria-recall-key'];
  if (typeof direct === 'string' && direct.trim()) return direct.trim();
  const auth = req.headers.authorization || '';
  const match = /^Bearer\s+(.+)$/i.exec(auth);
  return match ? match[1].trim() : '';
}

function safeEqual(a, b) {
  if (!a || !b) return false;
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

function authState(req) {
  const remote = req.socket.remoteAddress || '';
  if (isLoopback(remote)) return { ok: true, mode: 'loopback', remote };
  if (!SHARED_KEY) return { ok: false, mode: 'disabled', remote };
  if (!safeEqual(suppliedKey(req), SHARED_KEY)) return { ok: false, mode: 'shared-key', remote };
  const owner = String(req.headers['x-asolaria-owner-pid'] || '').trim();
  if (ALLOWED_OWNER_PIDS.length && !ALLOWED_OWNER_PIDS.includes(owner)) {
    return { ok: false, mode: 'owner-pid-denied', remote, owner };
  }
  return { ok: true, mode: 'shared-key-owner-pid', remote, owner };
}

function requireAuth(req, res) {
  const auth = authState(req);
  if (auth.ok) return true;
  json(res, {
    ok: false,
    error: 'ASOLARIA_RECALL_AUTH_REQUIRED',
    colony: COLONY,
    remote: auth.remote,
    auth_mode: auth.mode,
    hint: 'Send Authorization: Bearer <shared key> or X-Asolaria-Recall-Key. Do not put keys in URLs.',
  }, 401);
  return false;
}

function requestJson(target, key) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(target);
    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.request(parsed, {
      method: 'GET',
      timeout: 8000,
      headers: {
        accept: 'application/json',
        authorization: `Bearer ${key}`,
        'x-asolaria-owner-pid': OWNER_PID,
        'x-asolaria-colony': COLONY,
      },
    }, res => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', chunk => { body += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(body) });
        } catch (err) {
          reject(new Error(`bad json from ${target}: ${err.message}`));
        }
      });
    });
    req.on('timeout', () => req.destroy(new Error(`timeout from ${target}`)));
    req.on('error', reject);
    req.end();
  });
}

async function searchPeers(q, limit) {
  if (!SHARED_KEY) {
    return PEERS.map(peer => ({ name: peer.name, base: peer.base, ok: false, error: 'shared key not configured' }));
  }
  return Promise.all(PEERS.map(async peer => {
    const endpoint = `${peer.base}/api/search?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`;
    try {
      const result = await requestJson(endpoint, SHARED_KEY);
      return { name: peer.name, base: peer.base, ok: result.status === 200, status: result.status, result: result.body };
    } catch (err) {
      return { name: peer.name, base: peer.base, ok: false, error: err.message };
    }
  }));
}

function publicStatus() {
  const summary = readSummary();
  return {
    ok: true,
    schema: 'asolaria.recall.node.v1',
    colony: COLONY,
    owner_pid: OWNER_PID,
    bind: BIND,
    port: PORT,
    rows: index.length,
    summary,
    auth: {
      loopback_open: true,
      remote_requires_shared_key: true,
      remote_requires_owner_pid: Boolean(ALLOWED_OWNER_PIDS.length),
      key_configured: Boolean(SHARED_KEY),
      key_source: SHARED_KEY ? (process.env.ASOLARIA_RECALL_KEY ? 'env' : 'file') : 'missing',
      allowed_owner_pids: ALLOWED_OWNER_PIDS,
    },
    peers: PEERS.map(peer => ({ name: peer.name, base: peer.base })),
    corpus: {
      local_only: true,
      hbp: HBP,
      hbi: HBI,
      note: 'The engine can be published. The HBP/HBI corpus must not be published.',
    },
  };
}

function html(res) {
  const summary = readSummary();
  const body = `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Asolaria Recall + Atlas</title>
<style>
body{margin:0;background:#0b0d10;color:#e9edf2;font:14px/1.4 system-ui,Segoe UI,Arial,sans-serif}
header{padding:18px 22px;border-bottom:1px solid #28313b;background:#10151b;display:flex;gap:18px;align-items:flex-start;justify-content:space-between}
h1{margin:0;font-size:20px;letter-spacing:0}
.tag{color:#9fd3ff}.warn{color:#ffd28a}.ok{color:#95f0aa}
main{display:grid;grid-template-columns:360px 1fr;gap:0;min-height:calc(100vh - 79px)}
aside{border-right:1px solid #28313b;padding:18px;overflow:auto}
section{padding:18px;overflow:auto}
a{color:#9fd3ff}input{width:100%;box-sizing:border-box;background:#111820;color:#f5f7fa;border:1px solid #314151;padding:10px;border-radius:6px}
button{background:#1f6feb;color:#fff;border:0;border-radius:6px;padding:9px 11px;margin-top:8px;cursor:pointer}
pre{white-space:pre-wrap;word-break:break-word;background:#05070a;border:1px solid #28313b;border-radius:6px;padding:12px;min-height:240px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:14px 0}
.stat{background:#111820;border:1px solid #263442;border-radius:6px;padding:10px}
.small{font-size:12px;color:#a8b3bf}
</style>
<header>
  <div><h1>Asolaria Recall + Atlas</h1><div class="small">${COLONY} measured recall surface beside the live atlas server</div></div>
  <div class="small">Evidence: <span class="ok">${summary.evidence_tag || 'LOCAL'}</span> · Remote: <span class="warn">shared-key gated</span></div>
</header>
<main>
<aside>
  <b>3D Atlas</b>
  <p><a target="_blank" href="http://127.0.0.1:4790/acer-multi-cylinder-atlas.html">Multi-Cylinder Prime Atlas</a></p>
  <p><a target="_blank" href="http://127.0.0.1:4790/acer-scientific-voxel-atlas.html">Scientific 3D Voxel Atlas</a></p>
  <b>Recall Summary</b>
  <div class="grid">
    <div class="stat"><span class="tag">rows</span><br>${summary.rows || index.length}</div>
    <div class="stat"><span class="tag">seek</span><br>${summary.seek_tests_passed || 0}/${summary.seek_tests_total || 0}</div>
    <div class="stat"><span class="tag">sig</span><br>${summary.significance_rows || 0}</div>
    <div class="stat"><span class="tag">text</span><br>${summary.text_extracted_rows || 0}</div>
  </div>
  <p class="small">This page serves local bytes. Remote access requires a shared key. The engine is publishable; the HBP/HBI corpus stays private.</p>
  <p class="small">Acer's 591,286-row table remains an Acer-measured artifact until copied/cross-verified here.</p>
  <label>Search path / PID / identity / metric</label>
  <input id="q" value="significance">
  <button onclick="search()">Search Local</button>
  <button onclick="searchAll()">Search Linked Colonies</button>
  <button onclick="randomRow()">Random Seek</button>
</aside>
<section>
  <pre id="out">Ready. Try "significance", "mcp", "brown", "PID", "falcon", or paste a pid/bh value.</pre>
</section>
</main>
<script>
async function show(url){ const r=await fetch(url); document.getElementById('out').textContent=await r.text(); }
async function search(){ const q=document.getElementById('q').value; await show('/api/search?q='+encodeURIComponent(q)); }
async function searchAll(){ const q=document.getElementById('q').value; await show('/api/search-all?q='+encodeURIComponent(q)); }
async function randomRow(){ await show('/api/random'); }
</script>`;
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
  res.end(body);
}

http.createServer(async (req, res) => {
  const u = url.parse(req.url, true);
  try {
    if (req.method === 'OPTIONS') {
      res.writeHead(204, { 'cache-control': 'no-store' });
      return res.end();
    }
    if (u.pathname === '/') return html(res);
    if (u.pathname === '/api/health') return json(res, publicStatus());
    if (u.pathname === '/api/summary') {
      if (!requireAuth(req, res)) return;
      return json(res, readSummary());
    }
    if (u.pathname === '/api/peers') {
      if (!requireAuth(req, res)) return;
      return json(res, { colony: COLONY, peers: PEERS.map(peer => ({ name: peer.name, base: peer.base })) });
    }
    if (u.pathname === '/api/random') {
      if (!requireAuth(req, res)) return;
      const e = index[Math.floor(Math.random() * index.length)];
      return json(res, { colony: COLONY, index: e, row: seekRow(e) });
    }
    if (u.pathname === '/api/seek') {
      if (!requireAuth(req, res)) return;
      const key = String(u.query.pid || u.query.bh || '');
      const e = index.find(x => x.pid === key || x.bh === key);
      return json(res, { colony: COLONY, found: Boolean(e), index: e || null, row: e ? seekRow(e) : null });
    }
    if (u.pathname === '/api/search') {
      if (!requireAuth(req, res)) return;
      return json(res, { colony: COLONY, ...searchLocal(u.query.q, u.query.limit) });
    }
    if (u.pathname === '/api/search-all') {
      if (!requireAuth(req, res)) return;
      const q = String(u.query.q || '').toLowerCase();
      const limit = Math.max(1, Math.min(250, Number(u.query.limit || 50)));
      const local = { colony: COLONY, ...searchLocal(q, limit) };
      const peers = await searchPeers(q, limit);
      return json(res, { q, local, peers });
    }
    res.writeHead(404); res.end('not found');
  } catch (err) {
    res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' });
    res.end(err.stack || String(err));
  }
}).listen(PORT, BIND, () => {
  console.log(`ASOLARIA_RECALL_FRONTEND|url=http://${BIND}:${PORT}/|colony=${COLONY}|rows=${index.length}|remote_key=${SHARED_KEY ? 1 : 0}|peers=${PEERS.length}`);
});
