# Bilateral data-exchange + compare-via-matrix protocol

The two fabrics never trust a single vantage. Data is shared as **recipe + sha identity**, each side
**materializes on its own drives**, and the two sides **compare hers-to-mine** with the same
adversarial-correction discipline used in the NN repo.

## Roles
- **acer** — `DESKTOP-J99VCNH`, holds the SOVLINUX 2TB as `\\.\PHYSICALDRIVE2`; designated **raw-read host**
  (fabric tool-advisor verdict `raw-read → REDIRECT-TO-ACER`).
- **liris** — `DESKTOP-PTSQTIE`, sister organ (`:4944`), holds her own drives + her own SOVLINUX view.

## The compare surface = sector-sha attestation chain
`tools/usb-raw/substrate-sector-walk.ps1` reads a fixed set of LBAs (MBR, partition boot, mid-500GB,
continuity-tail sectors, last-sector-of-2TB) and emits a **chained HBP attestation**: per sector
`sha256` + `sha16` + boot-sig + `prev_row_hash`→`row_hash`. That chain is the byte-level fingerprint
of a USB. Two USBs are the-same-slice iff their sector-sha chains match at the compared LBAs.

## Round (yin-yang)
1. **acer**: run sector-walk on `PHYSICALDRIVE2` → commit the attestation `.hbp` to
   `artifacts/usb-sovlinux/acer/`. Compute model sha (`GEMMA-IDENTITY.sha256`).
2. **liris**: pull. Materialize Gemma (re-download public model, **verify sha** against the receipt).
   Run sector-walk on **her** SOVLINUX view → commit to `artifacts/usb-sovlinux/liris/`.
3. **compare (the matrix)**: diff the two attestation chains LBA-by-LBA + diff the model shas.
   - **match** → slice confirmed identical cross-vantage, tag `CONVERGED`.
   - **divergence** → do NOT canonize. Open an adversarial-correction round: which vantage is right,
     why (re-seat USB? partial write? different partition?), fix, re-walk, re-compare.
4. **engines watch**: every round emits an HBP event to the bus (`:4947` `send-hbp` → `inbox.hbp`)
   so hookwall → GNN → Shannon ingest it, held-safe (no auto-fire).

## Safety gates (from the fabric tool-advisor, W113)
- `raw-read` → REDIRECT-TO-ACER (allowed via `usb_raw_io.py --read`). **Read-only, ungated.**
- `raw-write` → REDIRECT-TO-ACER, **and** requires `--unsafe-write` + token `quintuple-2026-05-25`
  + a GREEN `substrate-preflight.mjs` + elevated shell. Never run casually.
- `mount-ro` → DEFER-TO-APEX (operator present = apex).
- `format` / `repartition` → **HARD-DENY**.

Raw device reads need an **elevated (admin) shell** — `WinError 5 = ACCESS DENIED` means re-run
elevated (e.g. operator runs it via the session `!` prefix).
