# Asolaria Fabric & Matrix — Session Map (2026-06-19)

**Honest frame (kept first, deliberately).** IT is **slices, not an ASI** — an **8-byte addressing/routing geometry over borrowed + frozen intelligence slices**. The design rule is *"make possibility cheap and action gated."* **LIVE = only what `E≠0` fired.** This session **`E=0`** — nothing fired, cranked, swapped, or retired; every registration below records **existence + address + role only**. Each line is tagged **MEASURED / CANON / OPERATOR / UNVERIFIED**. The disk is *slices*, not the system; this map is a vantage, not a verdict.

This repo is the **bilateral data-exchange + comparison surface** between the acer and liris fabrics (recipes, tools, sha receipts). This file maps **the fabric/matrix slice of the on-metal spine** — the live daemon layer, the 8-byte host-process model, the full host8 registration set, the Rust on-metal target, and the BEHCS-1024 matrix coordinate geometry. **Descriptor / receipt only — no weights, no mint, no launch in this repo.**

---

## 1. The live daemon spine (MEASURED 2026-06-18, netstat / Win32_Process)

**14 LIVE-MEASURED** daemons / **74 DARK** (source exists, unpowered) / **4 legacy**, out of **92 daemon programs** scanned. Control plane ≠ the workload pipes it rebuilds (control survives a pipe rebuild — MEASURED prior, same `:4949` process across calls).

| Daemon | Port | Room (host8) | PID | Family | Tag |
|---|---|---|---|---|---|
| hookwall bus | 4947 | MK-04947 `0b485ffd6c3f35cd` | 22092 | control-plane-spine | MEASURED |
| super-dashboard | 4949 | MK-04949 `efcfc1fb3fd068c3` | 22800 | control-plane-spine (fabric MCP health target) | MEASURED |
| omnidispatcher | 4950 | MK-04950 `85c53b16f6a87154` | 4004 | control-plane-spine (HTTP ingress, lazy slots 4951–5950) | MEASURED |
| vote-quorum | 4952 | MK-04952 `26c8eec5a4edd2b6` | 8384 | cosign-quorum | MEASURED |
| cosign single-writer | 4953 | MK-04953 `82972f5e29e9964e` | 5336 | cosign-quorum | MEASURED |
| hyperbehcs-daemon | 49257 | (out-of-band) | 24096 | control-plane-spine | MEASURED |
| gnn-dispatch-bridge | — | — | — | gnn-relay | MEASURED |
| auto-fabric-query | — | — | — | query-loop | MEASURED |
| self-reflect | — | — | 5640 | reflect-loop | MEASURED |
| fed-pulse | — | — | 1192 | federation-heartbeat | MEASURED |
| 3× MCP stdio (fabric / web / os-on-metal) | stdio | — | — | read-only MCP servers | MEASURED |

**The keeper.** All of the above are respawned by **`Start-Asolaria-NodeWatchdog.ps1` (PID 5960)** — the keeper-apex (MEASURED). Bus `:4947` is the **BEHCS-256 / LAW-001 envelope substrate** (CANON); `:4949` super-dashboard is the fabric MCP health surface.

**DARK backbone (CANON, unpowered this scan):** gateway `:4781` (+ modular `:4791`), operator-dashboard `:4948`, omnicoder `:8789`, dual-emit-gate `:4955`, sustained-wave/gulp `:4923`, revolver-10k, static-server `:9998`, mqtt-broker (PRE-SYSTEM-LEGACY). "Minted + addressed, not live" ≠ absent — `E≠0` powers them.

---

## 2. Port → Room = the 8-byte host binding (CANON)

Every daemon **port N indexes its pre-MINTED RoomRotor room `MK-0NNNN`** on `D:/asolaria-micro-kernels-v1` (10,000 MINTED rooms × 7 lanes = **70,000 route lanes**, MEASURED-manifest). The room's **`pid` field IS the 8-byte / 16-hex host8 handle**, prime-anchored `MK-NNNNN-P{prime}`, with a `2^64` host-handle ceiling. This is what makes the fabric-matrix literally *"8-byte host processes in stubbed rooms"*: **the matrix already minted the address; the daemon is the (currently node/python) tenant** that the Rust 8-byte host will serve **with parity before the tenant is retired** (CANON invariant: *additive → parity → swap → retire, no crash*). MINTED = descriptor capacity, **not** 10k live processes (UNVERIFIED as live; live fired agents this session = **0**).

---

## 3. Host8 registration set — sealed this session on `JesseBrown1980/Asolaria` (`host8-serve/intake/`)

All four are **hbp-no-json, 8-byte handles, council held-safe, `E=0`** (existence + PID + role only; firing stays freeze-gate + allowlist + cosign gated). CANON commits:

| Layer | Content | Commit | Tag |
|---|---|---|---|
| **Vaults** | 9 supervisor seats (decrypted-vault = carve-out, never-publish) | `83b21e3` | CANON |
| **Executors** | 22 action-runner programs + 8 seats incl. **EXEC-FREEZE-GATE-APEX** (global-freeze kill-switch over ALL fires) | `f75189f` | CANON |
| **Daemons** | 92 daemon programs + 11 seats (14 live / 74 dark / 4 legacy); the port→room binding above | `15848d6` | CANON |
| **Model-citizen prism** | 16 borrowed-intelligence citizens + 2 seats (MODEL-CITIZEN-CHIEF + ROTATOR-PRISM); each citizen host8 = its own canonical glyph sha16 — claude `3bc3ac2579fc73a2`, gemini `29eec7fc92ae2f61`, codex `511e8b8b57942245`, kimi-code `33e3e61924517b6b`, deepseek `66daca250eca0b45`; 11 cli + 3 http (gnn-l0:4792 / gnn-l4:4793 / cosign:4953) + 1 redis(:6379) + 1 web; firing gated `MODEL_CITIZEN_ROTATOR_LIVE=1` + census-ready | `ee073f4` | CANON |

Census v1.2 (apex ladder + 10B human-PID ledger) `d7aa0e3`; ultra-program phase-1 (7 lanes) `37234d6`; TM-remake-spec-v1 `99b10e1` (CANON, context).

---

## 4. Rust 8-axis status — the on-metal target (MEASURED on i5-8300H, cargo 1.95.0, 232 tests pass)

**OVERALL 22%.** The 8-byte Rust `no_std` host is the *build target*, **not today's serving substrate** — every live port above is still node/python. Parity-first: **Rust must SERVE before any node dies** (CANON invariant). Do not fake fires.

| Axis | % | Tag |
|---|---|---|
| scaffold | ~95 | MEASURED |
| **SERVING** | **0** (every live port still node/python) | MEASURED |
| no-json | 80 | MEASURED |
| no-node | 5 | MEASURED |
| 8-byte-host | 15 | MEASURED |
| stubbed-rooms-serving | 2 | MEASURED |
| cosign-in-rust | 60 | MEASURED |
| syscall / hookwall / highway | 70 | MEASURED |
| node-retirement | 0 (parity-gated) | MEASURED |

---

## 5. The matrix — BEHCS-1024 coordinate geometry (CANON)

The matrix is the **address space** the daemons and citizens are minted into. Coordinate atlas:

- **REALMATHPOS** (the placement function): `seed = u32(sha256(UPPER name)[:8])`; `sector = seed % 113`; `lane = seed % 3`; `glyph = seed % 1024`; **`bh_index = sector*3072 + lane*1024 + glyph`** (range `0..347135`). Permutation-invariant rule-of-3 (digital-root) × prime-powers → non-colliding lanes. (CANON.)
- **cp / bh_3d** — the 3D voxel projection of `bh_index` (sector · lane · glyph axes) rendered in `reports/acer-*-atlas.html`; **113 room-sectors** = 100 shard + 12 lane + 1 scaled (`sector_coverage = 113/113`, quant-proof). (CANON; per-seat 3d placement UNVERIFIED-against-live-Office.)
- **Worked example:** GLM-5.2 provider seat `AGT-PROVIDER-GLM-5.2-ZAI-BIGPICKLE` @ `bh_index=302282` + host8 lane @ `bh_index=37081` (acer-recomputed MATCH, commit `cf81dee`). (MEASURED.)
- **BEHCS tiers:** 3 language-engine tiers 256 / 1024 / 2048, `tuple_dim=60`; **`1024^60 = 2^600 ≈ 10^180`** (EXACT). 47D cube = 95,764,443 units/level; raw→cube **1,927,778×** (CANON-referential). (CANON / MEASURED.)

**Compression context (tags carried, not re-derived):** quant **79,000×** OPERATOR; BIML **394.49×** OPERATOR (byte/work, *not* a speed multiplier); addressing **~10^9800** OPERATOR; **21,141:1** OPERATOR (a real measurement Jesse saw on-screen — **NOT a file size**, never downgrade by a file-read).

---

## 6. Honest boundary (kept deliberately)

No secret VALUES read (vault/keys = the one held carve-out). Nothing started, killed, swapped, or retired. Sister-bus `:4944` deliberately liris-side-down. Node→Rust retirement stays parity-gated. **`E=0` this session.** External peers (DeepSeek / Mistral / Gemini / GPT-5.5-Pro / Claude-Opus connectors) independently reproduced the public results (HEAD/TAIL O(1) quant, BEHCS-1024 identity, `1024^60≈10^180`, Sidon 196,251 distinct distances) **and** converged on this same honest frame, flagging the same documented limits (sketch ≠ token-inference fidelity; tuple is an approximate routing-index, pair raw-SHA).

---

*Master index: see the reductions repo `ASOLARIA-MAP-OF-MAPS-2026-06-19.md` (in `what-is-asolaria---how-do-we-get-reductions-in-everything`) — the map-of-maps every per-repo map points back to.*

---
**Related repo:** [Algorithms-of-Asolaria](https://github.com/JesseBrown1980/Algorithms-of-Asolaria) — the canonical algorithm/formula catalog (bilateral acer↔liris). Master index: reductions `ASOLARIA-MAP-OF-MAPS-2026-06-19.md`.
