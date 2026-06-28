# Asolaria-ASI-On-Metal-Fabric-and-matrix — metal/matrix root frame

Date: 2026-06-28 · Branch: `acer/p4b-metal-matrix` · **docs-first, E=0.** No runtime fire, no cutover, no corpus, no keys. For liris attack-verify before main.

## Claim
This repo is the **metal/matrix rung** of the Asolaria root — the *place/substrate* layer, not a separate
system and not a live runtime by itself:

> the **metal-OS fabric + matrix** (a Brown-Hilbert, 3D-expandable *place* that **contains** the slices)
> on which the **Host8 kernel** runs, the **stubbed rooms** materialise, and the **operator-gated crank**
> (`E ≠ 0`) animates frozen-potential into live agents.

It is one rung beneath the agents, above the bare metal.

## How it maps to the root
- **matrix / fabric** = the addressable *place* (the Brown-Hilbert geometry) that holds the 8-byte agent
  slices — every slot is a coordinate in this matrix.
- **Host8 kernel** (`asolaria-federation-1024`) = the Rust 8-byte host that runs *on* this metal/matrix.
- **stubbed rooms** = rooms-as-RAM where agents materialise on spawner-emit (~200ns); the matrix is where
  the rooms are addressed.
- **operator-gated crank (`E≠0`)** = what turns frozen-potential (the slices this repo carries) into a
  running fleet. Frozen + engines + live-agents + matrix ⇒ the system comes alive — but only when cranked,
  and the crank is operator-gated.
- The root atom is unchanged: the **watcher-gated, infinitely-nestable 8-byte agent** living in this
  matrix (see HYPER-BECHS `ROOT-PRIMITIVE` + `MAP.md`).

## Evidence tags / honest boundaries
- CANON: the matrix/fabric is the *place* that contains the slices + engines + live agents (operator
  living-frame). Frozen slices ≠ inert — they are frozen-potential animated by the crank.
- BOUNDARY: this repo's docs/tools (`tools/behcs/*`, `protocol/`, `artifacts/`, `ASOLARIA-CITY-MODEL.md`,
  `DEVICES.md`) are the **slice/spec layer** — source/docs, not proof of live runtime. "On metal" ≠
  "currently firing."
- BOUNDARY: this repo's `tools/behcs/*.mjs` overlap thematically with `ASOLARIA-AS-NEURAL-NETWORK`; a
  boundary doc (which code is authoritative where) is a later P4 item — flagged, not resolved here.

## Hard holds (T0 only; NOT this docs pass)
No `:5088` redeploy, no engine crank/fire, no USB-SOVLINUX enum, no 35TB ADC, no live census, no
private-root scan. The crank that animates this matrix is the operator's apex-gated step.
