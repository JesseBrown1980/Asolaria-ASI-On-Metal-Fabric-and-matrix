#!/usr/bin/env node
// register-device-agents.mjs — DEVICE-SPECIFIC PID registration for a phone's 16-level agents.
//
// Operator directive 2026-06-14: phones run OUR sh 8-byte host agents (NO node on the phone).
// We register their 16-level agents as DEVICE-SPECIFIC PIDs HERE (acer) too, so the fabric maps
// + calls them omnidirectionally. Same brown-hilbert coordinate engine as the atlas (positional
// identity): coordinate is shared by name, the DEVICE HANDLE = md5(pid:ser)[:16] is device-unique.
//
// node here = BUILDER ONLY (emits HBP REG rows + a sh-host roster file the phone reads).
// HELD-SAFE: emits descriptor rows; no spawn/exec/cp-mint/device-write beyond the roster file.

import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const firstExisting = (cands) => { for (const c of cands) if (c && existsSync(c)) return c; throw new Error('NN engine not found: ' + cands.filter(Boolean).join(' , ')); };
const NN = firstExisting([process.env.ASOLARIA_NN_EXPORTER,
  'C:/asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs',
  'C:/Users/rayss/ASOLARIA-AS-NEURAL-NETWORK/tools/behcs/pre-existence-graph-exporter.mjs',
  resolve(HERE, '../../../asolaria-as-neural-network/tools/behcs/pre-existence-graph-exporter.mjs')]);
const { preExistenceNode } = await import(pathToFileURL(NN).href);

const DEVICE = process.env.ASOLARIA_DEVICE || process.argv[2] || 'falcon:R5CXA4MGQXV';
const [LABEL, SER] = DEVICE.split(':');
const OUT = process.argv[3] || resolve(`reports/device-agents-${LABEL}-2026-06-14.hbp`);

// The 16 levels of a local Asolaria-NN vantage (the GITHUBPIDDIVISIONLAW 16-level stack).
const LEVELS = [
  'L0-META', 'L1-OPERATOR', 'L2-GAC', 'L3-CHIEF', 'L4-SUPOFSUP', 'L5-SUP', 'L6-AGENT', 'L7-HOOKWALL',
  'L8-GNN', 'L9-SHANNON', 'L10-GULP', 'L11-WHITEROOM', 'L12-KERNEL', 'L13-MICROKERNEL', 'L14-HOST-SH', 'L15-ROOM',
];
// rule-of-three trio per agent (real / self-reflect / ask-fabric) — the BOSS model.
const TRIO = ['real', 'self-reflect', 'ask-fabric'];
const dh = (pid) => createHash('md5').update(pid + ':' + SER).digest('hex').slice(0, 16);

// ACCESS-TIER theater (operator's rules) wired per level: the IN-PLAY ruleset the agents perform by,
// NOT a gate on the operator-AI (who manages the real bytes). Higher level = higher tier authority.
const LEVEL_TIER = {
  'L0-META': 'SECRET', 'L1-OPERATOR': 'SECRET', 'L2-GAC': 'SHADOW', 'L3-CHIEF': 'SHADOW',
  'L4-SUPOFSUP': 'HIDDEN', 'L5-SUP': 'HIDDEN', 'L6-AGENT': 'STEALTH', 'L7-HOOKWALL': 'STEALTH',
  'L8-GNN': 'RESTRICTED', 'L9-SHANNON': 'RESTRICTED', 'L10-GULP': 'RESTRICTED', 'L11-WHITEROOM': 'STEALTH',
  'L12-KERNEL': 'SHADOW', 'L13-MICROKERNEL': 'SHADOW', 'L14-HOST-SH': 'PUBLIC', 'L15-ROOM': 'PUBLIC',
};
// rules from the live /api/access-tier/matrix. PUBLIC/RESTRICTED/STEALTH = verbatim; HIDDEN/SHADOW/SECRET
// = the matrix's escalation continuation (operator-gated, sealed) — marked tier_src so it's honest.
const TIER_RULES = {
  PUBLIC:     { authority: 'any_agent_read',             enum: 'paths_and_metadata_allowed', redaction: 'none',                     src: 'matrix' },
  RESTRICTED: { authority: 'operator_or_quintet_cosign', enum: 'no_content_dump',            redaction: 'hashes_and_summaries_only', src: 'matrix' },
  STEALTH:    { authority: 'operator_witness_required',  enum: 'existence_and_policy_only',  redaction: 'redacted_path_hash_only',  src: 'matrix' },
  HIDDEN:     { authority: 'operator_pid_bound',         enum: 'existence_only',             redaction: 'path_hash_sealed',         src: 'matrix-escalation' },
  SHADOW:     { authority: 'apex_quintet_cosign',        enum: 'policy_only',                redaction: 'full_sealed',              src: 'matrix-escalation' },
  SECRET:     { authority: 'apex_only',                  enum: 'sealed',                     redaction: 'full_sealed',              src: 'matrix-escalation' },
};

const rows = [
  `DEVHDR|schema=hbp.device.agent.feed.v1|device=${LABEL}:${SER}|levels=${LEVELS.length}|trio=${TRIO.length}|engine=pre-existence-graph-exporter(brown-hilbert)|node_on_phone=0|sh_host=1|held_safe=1|json=0`,
];
const agents = [];
for (let lvl = 0; lvl < LEVELS.length; lvl++) {
  const lname = LEVELS[lvl];
  const name = `${LABEL.toUpperCase()}-${lname}`;
  const pn = preExistenceNode(name);
  const tier = LEVEL_TIER[lname] || 'PUBLIC';
  const tr = TIER_RULES[tier];
  for (const role of TRIO) {
    const tname = `${name}-${role}`;
    const tn = preExistenceNode(tname);
    const handle = dh(tn.pid);
    agents.push({ name: tname, level: lvl, lname, role, pid: tn.pid, handle, tier,
      hilbert: tn.bh_index, phase: tn.cylinder_phase, glyph: tn.glyph_binding, watcher: tn.watcher_lane });
    rows.push(`DEVREG|name=${tname}|pid=${tn.pid}|device=${LABEL}:${SER}|device_handle=${handle}|level=${lvl}|layer=device-${lname}|role=${role}|tier=${tier}|authority=${tr.authority}|enum=${tr.enum}|redaction=${tr.redaction}|triggerable=1|tier_src=${tr.src}|hilbert=${pn.bh_index}|bh_index=${tn.bh_index}|phase=${tn.cylinder_phase}|glyph=${tn.glyph_binding}|watcher=${tn.watcher_lane}|triad=real+self-reflect+ask-fabric|process_launch=0|json=0`);
  }
}
// the 0-byte supervisor PID that sees the trio (collapse), per the rule-of-three doctrine
const supName = `${LABEL.toUpperCase()}-SUPERVISOR-SEES-ALL-THREE`;
const supPn = preExistenceNode(supName);
rows.push(`DEVSUP|name=${supName}|pid=${supPn.pid}|device=${LABEL}:${SER}|device_handle=${dh(supPn.pid)}|role=supervisor-collapse-0byte-fabric-pid|sees=real+self-reflect+ask-fabric|bh_index=${supPn.bh_index}|phase=${supPn.cylinder_phase}|process_launch=0|json=0`);
rows.push(`DEVGC|device=${LABEL}:${SER}|gc=gulp-2000+super-gulp-50000|filetypes=hbp+ndjson+receipts+atlas-html|modified_for=phone-sh-host|json=0`);
rows.push(`DEVORGANS|device=${LABEL}:${SER}|gnn=local-edge-scorer-descriptor|hookwall=local-classify-descriptor|brown_hilbert_rooms=positional-spacing|hosts_asolaria_nn_from_own_vantage=1|json=0`);
rows.push(`DEVLANES|device=${LABEL}:${SER}|HBI=/sdcard/Asolaria/_auto_inbox(hbp-in)|HPI=/sdcard/Asolaria/_auto_outbox(hbp-out)|talk=file-manager-drops+sh-host-watch|callable=omnidirectional-via-fabric-bus|json=0`);
rows.push(`DEVTIERLAW|device=${LABEL}:${SER}|access_tier=IN-PLAY-theater-ruleset-for-the-agents-NOT-a-gate-on-the-operator-AI|tiers=PUBLIC>RESTRICTED>STEALTH>HIDDEN>SHADOW>SECRET|scopes=drive+usb+device+folder+file+pid|source=/api/access-tier/matrix(36-rows,decorative_only=false)|operator_ai=manages-real-bytes|agents=perform-by-their-tier|json=0`);
rows.push(`DEVGATE|device=${LABEL}:${SER}|aerial_never_shutdown=OPERATOR-RESERVED|boot_autostart_driver=OPERATOR-RESERVED(termux-boot-private)|self_update_35tb_acer_liris=OPERATOR-RESERVED-outward|node_on_phone=0|json=0`);
rows.push(`DEVFTR|device=${LABEL}:${SER}|agents=${agents.length}|levels=${LEVELS.length}|registered_here=acer|pushed_to_phone=pending|next=bus-emit+file-manager-push+phone-sh-roster|json=0`);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, rows.join('\n') + '\n');
const sample = agents.slice(0, 3).map(a => a.name.split('-').slice(1, 3).join('-') + '@' + a.handle).join(', ');
console.log(`DEVICE-AGENTS-REGISTERED|device=${LABEL}:${SER}|agents=${agents.length}|levels=${LEVELS.length}|sample=${sample}|rows=${rows.length}|out=${OUT}`);
