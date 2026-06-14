#!/usr/bin/env node
// build-cli-stub-rooms.mjs — ground-up CLI agent stub rooms for a phone, sh-based (NO node on phone).
//
// Operator directive 2026-06-14: give the phones the CLI agents (Claude/Codex/OpenCode/Hermes/
// DeepSeek/Google) as STUB ROOMS they spawn into — empty terminal-shell folders, materialized ONLY
// when a spawner PID emits (AGENTCOSTLAW: ~0 cost until lit). Written in OUR language (HBP rows +
// glyph), talking through OUR pipes (the 8-byte sh host + the bus), connected to the PID/registration
// office. node = builder here only; the phone runs sh + the host CMD fills the stub at runtime.
//
// HELD-SAFE: emits descriptors + a held spawn-stub; the actual CLI auth/run is OPERATOR-GATED
// (subscription/install/ToS — never route bots through sub creds). process_launch=0 in every row.

import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const firstExisting = (c) => { for (const p of c) if (p && existsSync(p)) return p; throw new Error('NN engine missing: ' + c.filter(Boolean).join(' , ')); };
const NN = firstExisting([process.env.ASOLARIA_NN_EXPORTER,
  'C:/asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs',
  'C:/Users/rayss/ASOLARIA-AS-NEURAL-NETWORK/tools/behcs/pre-existence-graph-exporter.mjs',
  resolve(HERE, '../../../asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs')]);
const { preExistenceNode } = await import(pathToFileURL(NN).href);

const DEVICE = process.env.ASOLARIA_DEVICE || process.argv[2] || 'falcon:R5CXA4MGQXV';
const [LABEL, SER] = DEVICE.split(':');
const OUT = process.argv[3] || resolve(`reports/device-cli-rooms-${LABEL}-2026-06-14.hbp`);
const dh = (pid) => createHash('md5').update(pid + ':' + SER).digest('hex').slice(0, 16);

// The CLI agents + their REAL connector contract (in our language). cmd = how the host CMD fills the
// stub at runtime; provider/auth marked honestly; all RESTRICTED (they reach external providers).
const CLIS = [
  { id: 'claude',   cmd: 'claude',            provider: 'anthropic-subscription', auth: 'OAuth-operator-gated',   free: 0 },
  { id: 'codex',    cmd: 'codex',             provider: 'openai',                 auth: 'apikey-operator-gated',  free: 0 },
  { id: 'opencode', cmd: 'opencode run',      provider: 'opencode-free-models',   auth: 'ed25519-0-token',        free: 1 },
  { id: 'hermes',   cmd: 'hermes',            provider: 'asolaria-fabric-gateway', auth: 'fabric-bus',            free: 1 },
  { id: 'deepseek', cmd: 'opencode run --model opencode/deepseek-v4-flash-free', provider: 'deepseek-free', auth: 'ed25519-0-token', free: 1 },
  { id: 'google',   cmd: 'gemini',            provider: 'google-api',             auth: 'GEMINI_API_KEY-operator-gated', free: 0 },
];

const rows = [
  `CLIROOMHDR|schema=hbp.cli.stub.room.v1|device=${LABEL}:${SER}|clis=${CLIS.length}|model=stub-room-empty-until-spawner-pid-emit|node_on_phone=0|pipe=HBP+8byte-sh-host|lang=glyph+hbp|held_safe=1|json=0`,
  `CLIROOMLAW|agentcostlaw=room-is-0-cost-stub-until-materialized|materialize_on=spawner-PID-emit|host_cmd_fills_stub=1|process_launch=0|provider_terms_apply=1|no_bot_through_sub_creds=1|json=0`,
];
const rooms = [];
for (const c of CLIS) {
  const roomName = `${LABEL.toUpperCase()}-ROOM-CLI-${c.id.toUpperCase()}`;
  const pn = preExistenceNode(roomName);
  const handle = dh(pn.pid);
  rooms.push({ id: c.id, roomName, pid: pn.pid, handle, bh: pn.bh_index, phase: pn.cylinder_phase, glyph: pn.glyph_binding });
  // the connector descriptor — OUR language, OUR pipes, sh host fills it on emit
  rows.push(`CLIROOM|id=${c.id}|room=${roomName}|pid=${pn.pid}|device_handle=${handle}|cmd=${c.cmd}|provider=${c.provider}|auth=${c.auth}|free=${c.free}|tier=RESTRICTED|authority=operator_or_quintet_cosign|pipe=HBP-via-8byte-sh-host|lang=glyph+hbp|room_dir=/sdcard/Asolaria/rooms/${c.id}|inbox=/sdcard/Asolaria/rooms/${c.id}/_in|outbox=/sdcard/Asolaria/rooms/${c.id}/_out|spawn_on=spawner-pid-emit|node=0|process_launch=0|state=STUB_EMPTY_HELD|json=0`);
}
rows.push(`CLIROOMOFFICE|device=${LABEL}:${SER}|connect_to=D:/PID-Registration-Office+fabric-bus:4947|register=device-specific-room-PIDs|callable=omnidirectional|json=0`);
rows.push(`CLIROOMFTR|device=${LABEL}:${SER}|rooms=${rooms.length}|registered_here=acer|pushed_to_phone=pending|actual_cli_auth=OPERATOR-GATED|ground_up=asolaria-as-NN+fabric-matrix-on-phone|next=file-manager-push-room-folders+register-office+wire-host|json=0`);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, rows.join('\n') + '\n');
// also emit a tiny held spawn-stub sh (descriptor-only; real run is operator-gated) per room, as one bundle
const stub = `#!/system/bin/sh\n# CLI room spawn-stub (HELD): materializes ONLY when a spawner PID emits + operator authorizes.\n# Reads its room _in (HBP), would run the CLI cmd, writes _out (HBP). NO autostart. process_launch gated.\nROOM=$1; CMD=$2\n[ -z "$ROOM" ] && { echo "STUB-HELD|need=room|json=0"; exit 0; }\necho "CLIROOM-SPAWN-HELD|room=$ROOM|cmd=$CMD|state=awaiting-operator-emit|node=0|json=0"\n`;
writeFileSync(resolve(dirname(OUT), 'cli-room-spawn-stub.sh'), stub);
console.log(`CLI-STUB-ROOMS-BUILT|device=${LABEL}:${SER}|rooms=${rooms.length}|ids=${rooms.map(r => r.id).join('+')}|out=${OUT}`);
console.log('SAMPLE=' + JSON.stringify(rooms.slice(0, 2).map(r => ({ id: r.id, pid: r.pid.slice(0, 28), handle: r.handle }))));
