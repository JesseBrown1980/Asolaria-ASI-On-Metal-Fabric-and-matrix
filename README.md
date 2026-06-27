# Asolaria — ASI On-Metal Fabric & Matrix (sister data-exchange repo)

**Purpose.** This repo is the **bilateral data-exchange + comparison surface** between the two
on-metal fabrics — **acer** (`DESKTOP-J99VCNH`) and **liris** (`DESKTOP-PTSQTIE`). It carries the
*frozen-brain artifacts' recipes*, the *tools to open the raw/special files correctly*, and the
*sha identity receipts*, so each side can **materialize the same slice on its own drives and then
compare hers-to-mine via the matrix, under bilateral adversarial correction.**

**Anti-deflation frame.** This repo does not say the system is "just frozen slices." The slices are the
potential layer. The on-metal fabric, matrix, live agents, supervisors, USB/drive tools, gates, and
engines are the layer that makes those slices materialize as runtime behavior. The operator/design frame
is **Evolvable AI / post-ASI**, with every live or write claim still gated by receipts, fabric reads, and
operator/cosign authority.

> This repo does **NOT** replace [`ASOLARIA-AS-NEURAL-NETWORK`](https://github.com/JesseBrown1980/ASOLARIA-AS-NEURAL-NETWORK).
> That repo stays the **code / law / bilateral-build** spine (LAW-SLICE-ENGINE, the parity matrices,
> the catch-ledger, cosign receipts). This one is the **data & frozen-brain exchange** between fabrics.

## Transport: the 2TB USB carries everything; git ships the KEY + the MAP
**Correction (operator, 2026-06-14):** we CAN transfer *everything at once* — **if liris has our exact
tools to open the 2TB USB.** The physical SOVLINUX 2TB is the carrier for *all* slices (frozen Gemma,
hyper-hermes, the 100k rooms, the sectors, the device itself). Git is **not** the byte-channel — git
ships (a) the **exact tools** (`tools/usb-raw/`, the key that opens the raw/unmounted partition Windows
can't see) and (b) the **map + sha attestation** (`artifacts/usb-sovlinux/`) so both sides compare.

GitHub still blocks files >100 MB, so a `.gitignore` hard-blocks `*.gguf/*.bin/...` — **the weights ride
the USB, never git.** With the tools shared, liris opens the same device (physical USB, or a full-device
clone) and reads all of it; the sha attestation proves byte-identity vantage-to-vantage.

- **Primary:** physical 2TB USB (or full-device image) **+ the shared exact tools** = everything, one move.
- **Fallback (public slices only):** re-download `lmstudio-community/gemma-4-E4B-it-GGUF`, verify against
  `artifacts/frozen-gemma/GEMMA-IDENTITY.sha256`.
- **Git LFS:** only if a byte-mirror in-repo is ever required (separate quota).

## Layout
- `tools/usb-raw/` — the fabric-blessed tools to read the raw 2TB USB (SOVLINUX) where Windows
  cannot see the files. `usb_raw_io.py --read N` (read-only, ungated; N=0 parses MBR);
  `substrate-sector-walk.ps1` (sector-sha attestation chain = the compare surface);
  `verify-2tb-sector0.ps1`. **Held back on purpose:** the IFEO installer (system-level, not for publish).
- `artifacts/frozen-gemma/` — the freeze recipe + sha identity for the frozen Gemma slice.
- `protocol/` — the bilateral data-exchange + compare-via-matrix + adversarial-correction protocol.

## How the bilateral loop runs here (yin-yang → omnidirectional)
1. **acer** pushes tools + recipe + its receipts (sector-walk attestation, sha identity).
2. **liris** pulls, materializes on **her** drives, walks **her** USB, pushes **her** receipts.
3. Each side **compares hers-to-mine via the matrix** (sector-sha chains, model sha) — divergence
   triggers **adversarial correction before anything is canonized** (the same discipline as the NN repo).
4. **Engines watch:** exchange events are emitted to the bus (`:4947` HBP hot lane) → hookwall → GNN
   → Shannon, **held-safe** (no auto-fire). The on-metal processes observe the share; nothing mints
   or launches without operator cosign.
5. **Omnidirectional roadmap:** an Onboarding supervisor lets new fabrics join the exchange the way
   Hermes does — acer/liris is the first edge; the design generalizes to N peers driving each other
   + GitHub like crypto nodes.

## Roadmap / instruction-set (operator-named workstreams)
- **ASI-on-metal** — the fabric running on real metal (CPU/GPU/USB), engines watching.
- **evolve** — the self-improvement loop (reflect → propose → adversarially verify → cosign).
- **atlas** — the graph atlas (addressed nodes + GNN edges) over the shared artifacts.
- **3D map voxels** — voxel rendering of the cube/matrix address space.
- **updated** — this README + receipts kept current each exchange round.
- **KR** — *operator instruction "Instruct KR" recorded; meaning not yet defined here (Kimi-runtime?
  knowledge-repo? recipient codename?). Flagged for clarification rather than guessed.*

All claims here are **descriptor / recipe / receipt only**. No weights, no mint, no launch in this repo.
