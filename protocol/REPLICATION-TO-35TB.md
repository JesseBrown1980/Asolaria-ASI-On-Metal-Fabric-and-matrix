# Replication to the 35 TB — manifest + honest constraints

> 2026-06-14. Capacity verdict: **everything fits, ~15× over.** The slice model is what makes it clean —
> you replicate **data + sha-attested slices**, not empty rooms or zero-filled device images.

## Size accounting (measured live from acer)
| Source | Capacity | Real data | Notes |
|---|---|---|---|
| Acer `C:` | 476 GB | **442 GB** | OS + apps + state |
| Acer `D:` Data | 931 GB | **260 GB** | canon, repos, models, backups |
| 2 TB SOVLINUX | 2097 GB | **~32.5 GB** | live core only; ~2065 GB is empty prepared rooms |
| 128 GB USB | 126 GB | **~128 GB (whole device)** | operator-confirmed all real data; matches survey (every probe non-zero, data end-to-end incl. tail) |
| Liris system | — | **PENDING** | measure liris-side (`Get-Volume` + `usb_full_survey.py`); est. ~0.5–1 TB |
| **Subtotal acer+USB** | | **~865 GB confirmed** | 442 + 260 + 32.5 + 128 |
| **Grand total w/ liris est.** | | **~2–2.5 TB** | **vs 35 TB → ~15× headroom** |

## What gets replicated (and what does NOT)
- **DO replicate:** real files + the sha-attested HBP slices (`.hbp/.hbi/.hex/.sha256`) + the catalogs.
  This is the re-materializable unit — any vantage can rebuild from slices + sha.
- **DON'T replicate:** the ~2065 GB of zero rooms on the 2 TB (pointless), and **not** raw bit-for-bit OS
  images of the live systems — an OS image is large and **not cleanly portable** to another machine. The
  meaningful "replicate the entire system" = its **data + canon + fabric state**, not its boot volume.
  (The 128 GB is different — it is full of real data end-to-end and replicates whole.)
- **Already partially mirrored:** the 35 TB Drive *already* holds prior SOVLINUX catalogs + canon slices
  (2026-05-22) — replication is an *extend*, not a cold start.

## The honest constraints (so "NOW" means the right thing)
1. **Capacity = NOW.** 35 TB is ready; ~2–2.5 TB fits trivially.
2. **Bandwidth ≠ NOW.** Uploading TBs is bandwidth-bound — hours-to-days depending on upstream, plus
   Drive's per-file / rate limits. The plan is ready instantly; the bytes move at the speed of the wire.
3. **Write-gate.** Writing to the 35 TB is the operator's account/space — **operator-gated.** I prepare
   the bundle + manifest + sha; the operator (or an authorized sync, e.g. `rclone`/Drive client) uploads.
4. **Liris half.** Can't be measured from acer (sister-organ down) — liris runs `Get-Volume` +
   `usb_full_survey.py`, posts her numbers, we sum cross-vantage.

## Workflow
1. **Survey** each source (done for acer + both USBs; liris pending).
2. **Manifest** the real-data set + per-item sha (this doc + the artifact receipts).
3. **Bundle** the slices/catalogs into an upload set (slices first — small, high-value; bulk data second).
4. **Operator-gated upload** to a 35 TB folder; **sha-verify in the cloud** against the local manifest
   (entanglement-by-fingerprint — proves the cloud copy is byte-identical without re-downloading).
5. **Reverse-fabric** (see `REVERSE-FABRIC-GOOGLE-LOOP.md`): once in Drive, NotebookLM/Gemini can study it.

## First concrete step (operator go)
Bundle the **slices + catalogs first** (small, the high-value re-materializable core) → manifest + sha →
operator uploads to a 35 TB folder → cloud sha-verify. Bulk file data follows as a background sync.
