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
// Colony-derived basename: each colony serves its own corpus without filename collision.
// Defaults preserve the original liris deployment: ASOLARIA-LIRIS-RECALL.
const BASENAME = process.env.ASOLARIA_RECALL_BASENAME || `ASOLARIA-${COLONY.toUpperCase()}-RECALL`;
const HBP = path.join(DIR, `${BASENAME}.hbp`);
const HBI = path.join(DIR, `${BASENAME}.hbi`);
const SUMMARY = path.join(DIR, `SUMMARY-${COLONY.toUpperCase()}.json`);
const USE_INVERTED_INDEX = process.env.ASOLARIA_RECALL_INVERTED_INDEX !== '0';
const LINEAR_FALLBACK = process.env.ASOLARIA_RECALL_LINEAR_FALLBACK === '1';
const TERM_MIN = Math.max(1, Number(process.env.ASOLARIA_RECALL_TERM_MIN || 2));
const TERM_MAX = Math.max(TERM_MIN, Number(process.env.ASOLARIA_RECALL_TERM_MAX || 64));
const MAX_TERMS_PER_ROW = Math.max(8, Number(process.env.ASOLARIA_RECALL_MAX_TERMS_PER_ROW || 96));
const MAX_REFS_PER_TERM = Math.max(50, Number(process.env.ASOLARIA_RECALL_MAX_REFS_PER_TERM || 20000));
const KEY_FILE = process.env.ASOLARIA_RECALL_KEY_FILE
  || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.asolaria', 'recall.key');
const SHARED_KEY = loadSecret();
const PEERS = parsePeers(process.env.ASOLARIA_RECALL_PEERS || '');
const ALLOWED_OWNER_PIDS = parseCsv(process.env.ASOLARIA_RECALL_ALLOWED_OWNER_PIDS || 'OP-JESSE-PID,OP-RAYSSA-PID');
const MAX_SKEW_S = Math.max(1, Number(process.env.ASOLARIA_RECALL_MAX_SKEW_S || 120));
const LEVEL_PUBLIC = 0;
const LEVEL_FEDERATION = 5;
const LEVEL_OWNER_PRIVATE = 9;
const LINK_GRANTS = parseGrants(process.env.ASOLARIA_RECALL_GRANTS
  || ALLOWED_OWNER_PIDS.map(pid => `${pid}:${LEVEL_OWNER_PRIVATE}`).join(','));
// Comprehensive PII/secret path fragments, mirrored from Acer Rust level_tag after the
// 2026-06-22 full 591,286-row audit. Conservative by design: false positives only
// over-privatize rows; false negatives leak. Narrow slash-only forms are avoided so
// bare dirs/files also classify owner-private (for example ".asolaria", "dcim.json").
const PII_PATH_FRAGMENTS = [
  // legal / financial / customer / personal docs
  'legal',
  'evidence-package',
  'evidence',
  'google-support-refund',
  'support-refund-complaints',
  'refund-complaint',
  'refund',
  'bank',
  'invoice',
  'financial',
  'paypal',
  'zelle',
  'passport',
  'cnpj',
  'cpf',
  'whatsapp-rayssa',
  // secrets / keys / vault / credentials
  'beast-keys',
  'backup-keys',
  'decrypted-vault',
  'vault',
  'charm_',
  'private-key',
  'privatekey',
  'recall.key',
  '.pem',
  '.key',
  '.pk8',
  '.kdbx',
  '.keystore',
  '.jks',
  'id_rsa',
  'id_ed25519',
  'wallet.dat',
  'seed-phrase',
  'seed_phrase',
  'mnemonic',
  'credential',
  'secret',
  'password',
  'passwd',
  '.asolaria',
  // personal-device dumps
  'dcim',
  'sdcard',
  'falcon-dump',
  'phone-dump',
];
const PII_CONTENT_FRAGMENTS = [
  'cnpj',
  'cpf ',
  'paypal',
  'zelle',
  'refund complaint',
  'customer care',
  'passport no',
  'invoice #',
];
const PUBLIC_CANON_PATH_FRAGMENTS = [
  'asolaria-multi-cylinder',
  'scientific-voxel-atlas',
  'asolaria-real-model',
  'agentterms-os-dashboard',
  'asolaria-map-index',
  'archaeology-and-significance-canon',
  'brown-hilbert',
  'what-is-asolaria',
  'algorithms-of-asolaria',
  'session-update',
  'readme',
];

function parseCsv(raw) {
  return String(raw || '').split(',').map(x => x.trim()).filter(Boolean);
}

function clampAccessLevel(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return LEVEL_FEDERATION;
  return Math.max(LEVEL_PUBLIC, Math.min(LEVEL_OWNER_PRIVATE, Math.trunc(n)));
}

function parseLevel(raw, fallback = LEVEL_OWNER_PRIVATE) {
  if (raw === undefined || raw === null || raw === '') return fallback;
  return clampAccessLevel(raw);
}

function parseGrants(raw) {
  const grants = new Map();
  for (const part of parseCsv(raw)) {
    const i = part.lastIndexOf(':');
    if (i <= 0) continue;
    const owner = part.slice(0, i).trim();
    if (!owner) continue;
    grants.set(owner, clampAccessLevel(part.slice(i + 1)));
  }
  return grants;
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

function hasLongDigitRun(value) {
  return /\d{14,}/.test(String(value || ''));
}

function isPii(pathValue, contentValue) {
  const p = safeLowerPath(pathValue).replace(/\\/g, '/');
  const c = String(contentValue || '').toLowerCase();
  if (PII_PATH_FRAGMENTS.some(fragment => p.includes(fragment))) return true;
  if (PII_CONTENT_FRAGMENTS.some(fragment => c.includes(fragment))) return true;
  return hasLongDigitRun(contentValue);
}

function isPublicCanon(pathValue) {
  const p = safeLowerPath(pathValue).replace(/\\/g, '/');
  return PUBLIC_CANON_PATH_FRAGMENTS.some(fragment => p.includes(fragment));
}

function assignLevel(pathValue, contentValue) {
  if (isPii(pathValue, contentValue)) return LEVEL_OWNER_PRIVATE;
  if (isPublicCanon(pathValue)) return LEVEL_PUBLIC;
  return LEVEL_FEDERATION;
}

function readIndex() {
  if (!fs.existsSync(HBI)) return [];
  return fs.readFileSync(HBI, 'utf8').split(/\r?\n/).filter(line => line.startsWith('IDX|')).map(parseParts);
}

const index = readIndex();

function readRowFromFd(fd, entry) {
  if (!entry) return null;
  const buf = Buffer.alloc(Number(entry.len));
  fs.readSync(fd, buf, 0, buf.length, Number(entry.off));
  return buf.toString('utf8').trimEnd();
}

function seekRow(entry) {
  if (!entry) return null;
  const fd = fs.openSync(HBP, 'r');
  try {
    return readRowFromFd(fd, entry);
  } finally {
    fs.closeSync(fd);
  }
}

function tokenize(value) {
  const text = String(value || '').toLowerCase();
  const tokens = [];
  const push = token => {
    const t = String(token || '').slice(0, TERM_MAX);
    if (t.length >= TERM_MIN) tokens.push(t);
  };
  const re = /[a-z0-9][a-z0-9._:-]{0,127}/g;
  let m;
  while ((m = re.exec(text))) {
    const whole = m[0];
    push(whole);
    for (const part of whole.split(/[^a-z0-9]+/)) push(part);
  }
  return tokens;
}

function uniqueTokens(values, max = MAX_TERMS_PER_ROW) {
  const out = [];
  const seen = new Set();
  for (const value of values) {
    for (const token of tokenize(value)) {
      if (seen.has(token)) continue;
      seen.add(token);
      out.push(token);
      if (out.length >= max) return out;
    }
  }
  return out;
}

function addPosting(terms, term, ref) {
  let refs = terms.get(term);
  if (!refs) {
    refs = [];
    terms.set(term, refs);
  }
  if (refs.length < MAX_REFS_PER_TERM) refs.push(ref);
}

function buildInvertedIndex(entries) {
  const started = Date.now();
  const terms = new Map();
  const byPid = new Map();
  const byBh = new Map();
  const levelBuckets = new Map([[LEVEL_PUBLIC, []], [LEVEL_FEDERATION, []], [LEVEL_OWNER_PRIVATE, []]]);
  let rowBytes = 0;
  let postings = 0;
  let truncatedTerms = 0;
  let skippedRows = 0;

  if (!USE_INVERTED_INDEX || !fs.existsSync(HBP)) {
    return { ok: false, enabled: USE_INVERTED_INDEX, reason: 'disabled_or_missing_hbp', terms, byPid, byBh, levelBuckets };
  }

  const fd = fs.openSync(HBP, 'r');
  try {
    for (let i = 0; i < entries.length; i += 1) {
      const e = entries[i];
      let row = '';
      try {
        row = readRowFromFd(fd, e) || '';
      } catch {
        skippedRows += 1;
      }
      rowBytes += Buffer.byteLength(row);
      const level = assignLevel(e.path, row);
      e._level = level;
      if (levelBuckets.has(level)) levelBuckets.get(level).push(i);
      else levelBuckets.set(level, [i]);
      if (e.pid) byPid.set(e.pid, i);
      if (e.bh) byBh.set(String(e.bh).toLowerCase(), i);

      const before = terms.size;
      for (const term of uniqueTokens([e.pid, e.bh, e.path, row])) {
        addPosting(terms, term, i);
        postings += 1;
      }
      if (terms.size === before && row) truncatedTerms += 1;
    }
  } finally {
    fs.closeSync(fd);
  }

  return {
    ok: true,
    enabled: true,
    schema: 'HILBRA-IDX-BEHCS-TUPLE-TEXT-V1',
    json_hot_path: false,
    rows: entries.length,
    terms: terms.size,
    postings,
    row_bytes_indexed: rowBytes,
    skipped_rows: skippedRows,
    truncated_rows: truncatedTerms,
    built_ms: Date.now() - started,
    byPid,
    byBh,
    levelBuckets,
    termMap: terms,
  };
}

const inverted = buildInvertedIndex(index);

function intersectRefs(groups) {
  if (!groups.length) return [];
  groups.sort((a, b) => a.length - b.length);
  let current = new Set(groups[0]);
  for (const group of groups.slice(1)) {
    const next = new Set(group);
    current = new Set([...current].filter(x => next.has(x)));
    if (!current.size) break;
  }
  return [...current].sort((a, b) => a - b);
}

function refsForQuery(rawQuery) {
  const q = String(rawQuery || '').trim().toLowerCase();
  if (!q) return [...Array(index.length).keys()];
  if (inverted.byPid && inverted.byPid.has(q)) return [inverted.byPid.get(q)];
  if (inverted.byBh && inverted.byBh.has(q)) return [inverted.byBh.get(q)];
  const tokens = uniqueTokens([q], 16);
  if (!tokens.length) return [];
  const groups = [];
  for (const token of tokens) {
    const refs = inverted.termMap && inverted.termMap.get(token);
    if (!refs || !refs.length) return [];
    groups.push(refs);
  }
  return intersectRefs(groups);
}

function searchLocalLinear(rawQuery, rawLimit, maxLevel = LEVEL_OWNER_PRIVATE) {
  const q = String(rawQuery || '').toLowerCase();
  const limit = Math.max(1, Math.min(250, Number(rawLimit || 50)));
  const matches = [];
  for (const e of index) {
    if (matches.length >= limit) break;
    const indexHaystack = `${e.pid || ''} ${e.bh || ''} ${safeLowerPath(e.path || '')}`;
    let row = null;
    let hit = !q || indexHaystack.includes(q);
    if (!hit) {
      row = seekRow(e);
      hit = row.toLowerCase().includes(q);
    }
    if (!hit) continue;
    if (!row) row = seekRow(e);
    const level = assignLevel(e.path, row);
    if (level > maxLevel) continue;
    matches.push({ level, index: e, row });
  }
  return { q, count: matches.length, max_level: maxLevel, mode: 'linear-scan', matches };
}

function searchLocal(rawQuery, rawLimit, maxLevel = LEVEL_OWNER_PRIVATE) {
  if (!inverted.ok) return searchLocalLinear(rawQuery, rawLimit, maxLevel);
  const q = String(rawQuery || '').toLowerCase();
  const limit = Math.max(1, Math.min(250, Number(rawLimit || 50)));
  const matches = [];
  const refs = refsForQuery(q);
  for (const ref of refs) {
    if (matches.length >= limit) break;
    const e = index[ref];
    if (!e) continue;
    const level = Number.isInteger(e._level) ? e._level : assignLevel(e.path, seekRow(e));
    if (level > maxLevel) continue;
    const row = seekRow(e);
    matches.push({ level, index: e, row });
  }
  if (!matches.length && LINEAR_FALLBACK) return searchLocalLinear(rawQuery, rawLimit, maxLevel);
  return {
    q,
    count: matches.length,
    max_level: maxLevel,
    mode: 'inverted-index',
    index_schema: inverted.schema,
    candidate_count: refs.length,
    matches,
  };
}

function seekLocal(key, maxLevel = LEVEL_OWNER_PRIVATE) {
  let e = null;
  const lowered = String(key || '').toLowerCase();
  if (inverted.ok && inverted.byPid.has(String(key))) e = index[inverted.byPid.get(String(key))];
  else if (inverted.ok && inverted.byBh.has(lowered)) e = index[inverted.byBh.get(lowered)];
  else e = index.find(x => x.pid === key || x.bh === key);
  if (!e) return { found: false, index: null, row: null };
  const row = seekRow(e);
  const level = assignLevel(e.path, row);
  if (level > maxLevel) return { found: false, denied: true, level, max_level: maxLevel, index: null, row: null };
  return { found: true, level, index: e, row };
}

function randomLocal(maxLevel = LEVEL_OWNER_PRIVATE) {
  if (inverted.ok) {
    const refs = [];
    for (const [level, bucket] of inverted.levelBuckets.entries()) {
      if (level <= maxLevel) refs.push(...bucket);
    }
    if (!refs.length) return { found: false, index: null, row: null, max_level: maxLevel };
    const e = index[refs[Math.floor(Math.random() * refs.length)]];
    const row = seekRow(e);
    const level = Number.isInteger(e._level) ? e._level : assignLevel(e.path, row);
    return { found: true, level, max_level: maxLevel, mode: 'inverted-index-bucket', index: e, row };
  }
  const candidates = [];
  for (const e of index) {
    const row = seekRow(e);
    const level = assignLevel(e.path, row);
    if (level <= maxLevel) candidates.push({ e, row, level });
  }
  if (!candidates.length) return { found: false, index: null, row: null, max_level: maxLevel };
  const picked = candidates[Math.floor(Math.random() * candidates.length)];
  return { found: true, level: picked.level, max_level: maxLevel, index: picked.e, row: picked.row };
}

function json(res, obj, status = 200) {
  const body = JSON.stringify(obj, null, 2);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
  });
  res.end(body);
}

function hbpEscape(value) {
  return String(value ?? '')
    .replace(/\r/g, '\\r')
    .replace(/\n/g, '\\n')
    .replace(/\|/g, '%7C');
}

function hbpLine(kind, fields) {
  const parts = [kind];
  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue;
    parts.push(`${key}=${hbpEscape(value)}`);
  }
  parts.push('json=0');
  return `${parts.join('|')}\n`;
}

function hbp(res, body, status = 200) {
  res.writeHead(status, {
    'content-type': 'text/plain; charset=utf-8',
    'cache-control': 'no-store',
  });
  res.end(body);
}

function rowSha16(row) {
  return crypto.createHash('sha256').update(String(row || '')).digest('hex').slice(0, 16);
}

function hbpHealth(status) {
  let body = hbpLine('HILBRAHEALTH', {
    colony: status.colony,
    owner_pid: status.owner_pid,
    bind: status.bind,
    port: status.port,
    rows: status.rows,
    key_configured: status.auth.key_configured ? 1 : 0,
    peers: status.peers.length,
  });
  body += hbpLine('HILBRAIDX', {
    enabled: status.search_index.enabled ? 1 : 0,
    schema: status.search_index.schema || '',
    rows: status.search_index.rows || 0,
    terms: status.search_index.terms || 0,
    postings: status.search_index.postings || 0,
    built_ms: status.search_index.built_ms || 0,
    json_hot_path: status.search_index.json_hot_path ? 1 : 0,
  });
  for (const peer of status.peers) {
    body += hbpLine('HILBRAPEER', { name: peer.name, base: peer.base });
  }
  return body;
}

function hbpSearch(colony, access, result) {
  let body = hbpLine('HILBRASEARCH', {
    colony,
    q: result.q,
    count: result.count,
    max_level: result.max_level,
    mode: result.mode || 'unknown',
    index_schema: result.index_schema || '',
    candidate_count: result.candidate_count ?? '',
    access_mode: access.mode || '',
    access_max_level: access.max_level ?? '',
    grant_level: access.grant_level ?? '',
  });
  for (let i = 0; i < result.matches.length; i += 1) {
    const match = result.matches[i];
    const idx = match.index || {};
    body += hbpLine('HILBRAMATCH', {
      i,
      level: match.level,
      pid: idx.pid,
      bh: idx.bh,
      path: idx.path,
      off: idx.off,
      len: idx.len,
      row_sha16: rowSha16(match.row),
    });
  }
  return body;
}

function isLoopback(remoteAddress) {
  return remoteAddress === '127.0.0.1'
    || remoteAddress === '::1'
    || remoteAddress === '::ffff:127.0.0.1';
}

function hmacHex(key, ownerPid, host, verb, nonce, tsUnixS) {
  const ts = Buffer.alloc(8);
  ts.writeBigUInt64BE(BigInt(tsUnixS));
  return crypto.createHmac('sha256', Buffer.from(String(key)))
    .update('LINK|')
    .update(String(ownerPid))
    .update('|')
    .update(String(host))
    .update('|')
    .update(String(verb))
    .update('|')
    .update(String(nonce))
    .update('|')
    .update(ts)
    .digest('hex');
}

function safeEqual(a, b) {
  if (!a || !b) return false;
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

function randomNonce() {
  return crypto.randomBytes(16).toString('hex');
}

function linkHeaders(verb) {
  const ts = Math.floor(Date.now() / 1000);
  const nonce = randomNonce();
  const hmac = hmacHex(SHARED_KEY, OWNER_PID, COLONY, verb, nonce, ts);
  return {
    'x-asolaria-owner-pid': OWNER_PID,
    'x-asolaria-colony': COLONY,
    'x-asolaria-verb': verb,
    'x-asolaria-nonce': nonce,
    'x-asolaria-ts': String(ts),
    'x-asolaria-hmac': hmac,
  };
}

function authState(req, expectedVerb) {
  const remote = req.socket.remoteAddress || '';
  if (isLoopback(remote)) return { ok: true, mode: 'loopback', remote, owner: OWNER_PID, host: COLONY };
  if (!SHARED_KEY) return { ok: false, mode: 'disabled', remote };
  const owner = String(req.headers['x-asolaria-owner-pid'] || '').trim();
  const host = String(req.headers['x-asolaria-colony'] || req.headers['x-asolaria-host'] || '').trim();
  const verb = String(req.headers['x-asolaria-verb'] || '').trim();
  const nonce = String(req.headers['x-asolaria-nonce'] || '').trim();
  const tsRaw = String(req.headers['x-asolaria-ts'] || '').trim();
  const hmac = String(req.headers['x-asolaria-hmac'] || '').trim();
  if (!owner || !host || !verb || !nonce || !/^\d+$/.test(tsRaw) || !/^[0-9a-f]{64}$/.test(hmac)) {
    return { ok: false, mode: 'hmac-malformed', remote, owner };
  }
  if (verb !== expectedVerb) return { ok: false, mode: 'verb-mismatch', remote, owner, verb, expectedVerb };
  const ts = Number(tsRaw);
  const now = Math.floor(Date.now() / 1000);
  if (!Number.isSafeInteger(ts) || Math.abs(now - ts) > MAX_SKEW_S) {
    return { ok: false, mode: 'hmac-stale', remote, owner };
  }
  if (ALLOWED_OWNER_PIDS.length && !ALLOWED_OWNER_PIDS.includes(owner)) {
    return { ok: false, mode: 'owner-pid-denied', remote, owner };
  }
  const expected = hmacHex(SHARED_KEY, owner, host, verb, nonce, ts);
  if (!safeEqual(hmac, expected)) return { ok: false, mode: 'bad-hmac', remote, owner };
  return { ok: true, mode: 'hmac-owner-pid', remote, owner, host, verb };
}

function requireAuth(req, res, expectedVerb) {
  const auth = authState(req, expectedVerb);
  if (auth.ok) return auth;
  json(res, {
    ok: false,
    error: 'ASOLARIA_RECALL_AUTH_REQUIRED',
    colony: COLONY,
    remote: auth.remote,
    auth_mode: auth.mode,
    hint: 'Send HMAC headers: X-Asolaria-Owner-PID, X-Asolaria-Colony, X-Asolaria-Verb, X-Asolaria-Nonce, X-Asolaria-TS, X-Asolaria-HMAC. Do not put keys in URLs or on the wire.',
  }, 401);
  return null;
}

function grantedLevel(owner) {
  if (!owner) return null;
  return LINK_GRANTS.has(owner) ? LINK_GRANTS.get(owner) : null;
}

function effectiveLevel(auth, rawRequestedLevel) {
  const requested = parseLevel(rawRequestedLevel, LEVEL_OWNER_PRIVATE);
  if (auth.mode === 'loopback') {
    return { ok: true, requested, max_level: requested, grant_level: LEVEL_OWNER_PRIVATE };
  }
  const grant = grantedLevel(auth.owner);
  if (grant === null) return { ok: false, requested, max_level: null, grant_level: null };
  return { ok: true, requested, max_level: Math.min(requested, grant), grant_level: grant };
}

function accessDenied(res, auth, level) {
  return json(res, {
    ok: false,
    error: 'ASOLARIA_RECALL_LEVEL_DENIED',
    colony: COLONY,
    owner: auth.owner,
    requested_level: level.requested,
    grant_level: level.grant_level,
  }, 403);
}

function requestJson(target, verb) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(target);
    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.request(parsed, {
      method: 'GET',
      timeout: 8000,
      headers: {
        accept: 'application/json',
        ...linkHeaders(verb),
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

async function searchPeers(q, limit, level) {
  if (!SHARED_KEY) {
    return PEERS.map(peer => ({ name: peer.name, base: peer.base, ok: false, error: 'shared key not configured' }));
  }
  return Promise.all(PEERS.map(async peer => {
    const endpoint = `${peer.base}/api/search?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}&level=${encodeURIComponent(level)}`;
    try {
      const result = await requestJson(endpoint, 'search');
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
      remote_requires_hmac_sha256: true,
      remote_requires_owner_pid: Boolean(ALLOWED_OWNER_PIDS.length),
      key_configured: Boolean(SHARED_KEY),
      key_source: SHARED_KEY ? (process.env.ASOLARIA_RECALL_KEY ? 'env' : 'file') : 'missing',
      allowed_owner_pids: ALLOWED_OWNER_PIDS,
      grants: Object.fromEntries(LINK_GRANTS.entries()),
      max_skew_s: MAX_SKEW_S,
      canonical_message: 'LINK|owner_pid|host|verb|nonce|ts_unix_s_be64',
    },
    access_levels: {
      public: LEVEL_PUBLIC,
      federation: LEVEL_FEDERATION,
      owner_private: LEVEL_OWNER_PRIVATE,
      public_search_endpoint: '/api/public/search?q=...',
      invariant: 'PII rules win before public-canon rules; level 0 is the public portal.',
    },
    search_index: inverted.ok ? {
      enabled: true,
      schema: inverted.schema,
      json_hot_path: false,
      rows: inverted.rows,
      terms: inverted.terms,
      postings: inverted.postings,
      built_ms: inverted.built_ms,
      skipped_rows: inverted.skipped_rows,
      linear_fallback: LINEAR_FALLBACK,
    } : {
      enabled: false,
      reason: inverted.reason || 'unavailable',
      linear_fallback: true,
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
.auth{border:1px solid #314151;border-radius:6px;padding:10px;margin:12px 0;background:#0e141b}
.auth input{margin-top:6px}
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
  <p class="small">This page serves local bytes. Remote access requires HMAC + owner PID. The engine is publishable; the HBP/HBI corpus stays private.</p>
  <p class="small">Access levels: <span class="ok">0 public</span> · <span class="tag">5 federation</span> · <span class="warn">9 owner-private</span>. PII rules win before public-canon rules.</p>
  <p class="small">Acer's 591,286-row table remains an Acer-measured artifact until copied/cross-verified here.</p>
  <div class="auth">
    <b>Remote Colony Login</b>
    <p class="small">For LAN/browser use from another trusted machine. The key signs HMAC locally in this page; it is never sent as a raw key.</p>
    <input id="owner" placeholder="Owner PID" value="OP-JESSE-PID">
    <input id="host" placeholder="Calling colony" value="acer">
    <input id="secret" placeholder="Shared key" type="password">
    <button onclick="saveAuth()">Save Local Login</button>
    <button onclick="clearAuth()">Clear</button>
    <div id="authState" class="small"></div>
  </div>
  <label>Search path / PID / identity / metric</label>
  <input id="q" value="significance">
  <label class="small">Requested access level</label>
  <input id="level" value="0">
  <button onclick="publicSearch()">Search Public L0</button>
  <button onclick="search()">Search Local</button>
  <button onclick="searchAll()">Search Linked Colonies</button>
  <button onclick="randomRow()">Random Seek</button>
</aside>
<section>
  <pre id="out">Ready. Try "significance", "mcp", "brown", "PID", "falcon", or paste a pid/bh value.</pre>
</section>
</main>
<script>
const enc = new TextEncoder();
function isLoopback(){ return ['127.0.0.1','localhost','::1'].includes(location.hostname); }
function loadAuth(){
  document.getElementById('owner').value = localStorage.getItem('asolaria.recall.owner') || document.getElementById('owner').value;
  document.getElementById('host').value = localStorage.getItem('asolaria.recall.host') || document.getElementById('host').value;
  document.getElementById('secret').value = sessionStorage.getItem('asolaria.recall.key') || '';
  renderAuthState();
}
function saveAuth(){
  localStorage.setItem('asolaria.recall.owner', document.getElementById('owner').value.trim());
  localStorage.setItem('asolaria.recall.host', document.getElementById('host').value.trim());
  sessionStorage.setItem('asolaria.recall.key', document.getElementById('secret').value);
  renderAuthState();
}
function clearAuth(){
  sessionStorage.removeItem('asolaria.recall.key');
  document.getElementById('secret').value = '';
  renderAuthState();
}
function renderAuthState(){
  const has = Boolean(sessionStorage.getItem('asolaria.recall.key') || document.getElementById('secret').value);
  document.getElementById('authState').textContent = isLoopback()
    ? 'Loopback UI is open. Remote HMAC login optional for peer calls.'
    : (has ? 'HMAC login loaded for this tab.' : 'Remote search needs the shared key in this tab.');
}
function hex(bytes){ return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join(''); }
function concat(parts){
  const len = parts.reduce((n,p)=>n+p.length,0);
  const out = new Uint8Array(len);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}
function u64be(n){
  const b = new Uint8Array(8);
  new DataView(b.buffer).setBigUint64(0, BigInt(n), false);
  return b;
}
async function authHeaders(verb){
  if (isLoopback() && !sessionStorage.getItem('asolaria.recall.key') && !document.getElementById('secret').value) return {};
  const key = sessionStorage.getItem('asolaria.recall.key') || document.getElementById('secret').value;
  const owner = document.getElementById('owner').value.trim();
  const host = document.getElementById('host').value.trim();
  if (!key || !owner || !host) throw new Error('Remote search needs owner PID, colony, and shared key.');
  const nonceBytes = crypto.getRandomValues(new Uint8Array(16));
  const nonce = hex(nonceBytes);
  const ts = Math.floor(Date.now()/1000);
  const msg = concat([enc.encode('LINK|'), enc.encode(owner), enc.encode('|'), enc.encode(host), enc.encode('|'), enc.encode(verb), enc.encode('|'), enc.encode(nonce), enc.encode('|'), u64be(ts)]);
  const k = await crypto.subtle.importKey('raw', enc.encode(key), {name:'HMAC', hash:'SHA-256'}, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', k, msg);
  return {
    'X-Asolaria-Owner-PID': owner,
    'X-Asolaria-Colony': host,
    'X-Asolaria-Verb': verb,
    'X-Asolaria-Nonce': nonce,
    'X-Asolaria-TS': String(ts),
    'X-Asolaria-HMAC': hex(mac),
  };
}
async function show(url, verb){
  try {
    const r = await fetch(url, {headers: await authHeaders(verb)});
    document.getElementById('out').textContent=await r.text();
  } catch (err) {
    document.getElementById('out').textContent=String(err && err.message || err);
  }
}
async function showOpen(url){
  try {
    const r = await fetch(url);
    document.getElementById('out').textContent=await r.text();
  } catch (err) {
    document.getElementById('out').textContent=String(err && err.message || err);
  }
}
function requestedLevel(){ return document.getElementById('level').value || '0'; }
async function publicSearch(){ const q=document.getElementById('q').value; await showOpen('/api/public/search?q='+encodeURIComponent(q)+'&level=0'); }
async function search(){ const q=document.getElementById('q').value; await show('/api/search?q='+encodeURIComponent(q)+'&level='+encodeURIComponent(requestedLevel()), 'search'); }
async function searchAll(){ const q=document.getElementById('q').value; await show('/api/search-all?q='+encodeURIComponent(q)+'&level='+encodeURIComponent(requestedLevel()), 'search-all'); }
async function randomRow(){ await show('/api/random?level='+encodeURIComponent(requestedLevel()), 'random'); }
loadAuth();
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
    if (u.pathname === '/api/health.hbp') return hbp(res, hbpHealth(publicStatus()));
    if (u.pathname === '/api/public/search') {
      return json(res, { colony: COLONY, access: { mode: 'public', max_level: LEVEL_PUBLIC }, ...searchLocal(u.query.q, u.query.limit, LEVEL_PUBLIC) });
    }
    if (u.pathname === '/api/public/search.hbp') {
      const access = { mode: 'public', max_level: LEVEL_PUBLIC };
      return hbp(res, hbpSearch(COLONY, access, searchLocal(u.query.q, u.query.limit, LEVEL_PUBLIC)));
    }
    if (u.pathname === '/api/summary') {
      const auth = requireAuth(req, res, 'summary');
      if (!auth) return;
      return json(res, readSummary());
    }
    if (u.pathname === '/api/peers') {
      const auth = requireAuth(req, res, 'peers');
      if (!auth) return;
      return json(res, { colony: COLONY, peers: PEERS.map(peer => ({ name: peer.name, base: peer.base })) });
    }
    if (u.pathname === '/api/random') {
      const auth = requireAuth(req, res, 'random');
      if (!auth) return;
      const level = effectiveLevel(auth, u.query.level);
      if (!level.ok) return accessDenied(res, auth, level);
      return json(res, { colony: COLONY, access: level, ...randomLocal(level.max_level) });
    }
    if (u.pathname === '/api/seek') {
      const auth = requireAuth(req, res, 'seek');
      if (!auth) return;
      const level = effectiveLevel(auth, u.query.level);
      if (!level.ok) return accessDenied(res, auth, level);
      const key = String(u.query.pid || u.query.bh || '');
      return json(res, { colony: COLONY, access: level, ...seekLocal(key, level.max_level) });
    }
    if (u.pathname === '/api/search') {
      const auth = requireAuth(req, res, 'search');
      if (!auth) return;
      const level = effectiveLevel(auth, u.query.level);
      if (!level.ok) return accessDenied(res, auth, level);
      return json(res, { colony: COLONY, access: level, ...searchLocal(u.query.q, u.query.limit, level.max_level) });
    }
    if (u.pathname === '/api/search.hbp') {
      const auth = requireAuth(req, res, 'search');
      if (!auth) return;
      const level = effectiveLevel(auth, u.query.level);
      if (!level.ok) return accessDenied(res, auth, level);
      return hbp(res, hbpSearch(COLONY, level, searchLocal(u.query.q, u.query.limit, level.max_level)));
    }
    if (u.pathname === '/api/search-all') {
      const auth = requireAuth(req, res, 'search-all');
      if (!auth) return;
      const level = effectiveLevel(auth, u.query.level);
      if (!level.ok) return accessDenied(res, auth, level);
      const q = String(u.query.q || '').toLowerCase();
      const limit = Math.max(1, Math.min(250, Number(u.query.limit || 50)));
      const local = { colony: COLONY, access: level, ...searchLocal(q, limit, level.max_level) };
      const peers = await searchPeers(q, limit, level.max_level);
      return json(res, { q, access: level, local, peers });
    }
    res.writeHead(404); res.end('not found');
  } catch (err) {
    res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' });
    res.end(err.stack || String(err));
  }
}).listen(PORT, BIND, () => {
  console.log(`ASOLARIA_RECALL_FRONTEND|url=http://${BIND}:${PORT}/|colony=${COLONY}|rows=${index.length}|remote_key=${SHARED_KEY ? 1 : 0}|peers=${PEERS.length}`);
});
