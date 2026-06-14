# Asolaria — ASI On-Metal Fabric & Matrix (sister data-exchange repo)

**Purpose.** This repo is the **bilateral data-exchange + comparison surface** between the two
on-metal fabrics — **acer** (`DESKTOP-J99VCNH`) and **liris** (`DESKTOP-PTSQTIE`). It carries the
*frozen-brain artifacts' recipes*, the *tools to open the raw/special files correctly*, and the
*sha identity receipts*, so each side can **materialize the same slice on its own drives and then
compare hers-to-mine via the matrix, under bilateral adversarial correction.**

> This repo does **NOT** replace [`ASOLARIA-AS-NEURAL-NETWORK`](https://github.com/JesseBrown1980/ASOLARIA-AS-NEURAL-NETWORK).
> That repo stays the **code / law / bilateral-build** spine (LAW-SLICE-ENGINE, the parity matrices,
> the catch-ledger, cosign receipts). This one is the **data & frozen-brain exchange** between fabrics.

## Hard rule: no large binaries in git
GitHub blocks files >100 MB. The frozen models are **5–6 GB** and **do not go in git**.
A `.gitignore` hard-blocks `*.gguf / *.bin / *.onnx / *.safetensors / *.pt / *.ab` so neither side
can accidentally commit weights. **We ship the coordinate + recipe + sha identity; each fabric
renders the same frozen slice from the public source, and the sha proves byte-identity.** This is
the slice-native transport: ship the address and the recipe, not the bytes.

Binary transport options (operator's call):
1. **Re-download + sha-verify (default, $0, git-native):** liris pulls the public
   `lmstudio-community/gemma-4-E4B-it-GGUF`, verifies against `artifacts/frozen-gemma/GEMMA-IDENTITY.sha256`.
2. **Physical USB:** the SOVLINUX 2TB master copy is the sovereignty cold-storage transfer medium.
3. **Git LFS:** only if a true byte-mirror in-repo is required (separate quota).

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
