# Asolaria Fabric & Matrix — Layered Census (substrate / route / storage slice), 2026-06-18

Built under the **ANTI-DEFLATION COUNT LAW** (canon in the reductions repo `canon/laws/ANTI-DEFLATION-COUNT-LAW.md`). Source: census workflow `wd710opm4` (9 agents) + raw-USB read via `tools/usb-raw/usb_raw_io.py`. **No single total — by layer, tagged MEASURED / CANON / MODEL / UNVERIFIED.** Live = only `E≠0`.

## Substrate / route / storage layers

- **L6 — premade PID substrate:** `D:/asolaria-100B-new-run-2026-06-15/checkpoint.state.json` = **100,000,000,000 packets** (MEASURED-complete; 100k chunks, 280,036,550 genius + 279,992,736 mistake marks, `childProcessSpawns=0 / externalModelTokens=0`). = address-space capacity + deterministic marks, **not** 100B live agents.
- **L7 — route capacity:** `D:/asolaria-micro-kernels-v1/manifest.hbp` = **10,000 MINTED RoomRotor rooms × 7 lanes = 70,000 route lanes**; each = an 8-byte/16-hex host handle, prime-anchored `MK-NNNNN-P{prime}`; **2⁶⁴ host-handle ceiling**; omnidispatcher 1000 lazy ports; 8 fabric-revolver chambers (`auto_fire=false`). MINTED = descriptor capacity, **not** 10k processes; the Rust 8-byte `no_std` host is **phase-3 scaffold** (build target — must SERVE before any node dies).
- **L8 — matrix store / storage:**
  - **REALMATHPOS** coordinate atlas: `seed=u32(sha256(UPPER name)[:8])`; `sector=seed%113`; `lane=seed%3`; `glyph=seed%1024`; `bh_index=sector*3072+lane*1024+glyph` (0..347135).
  - **GLM-5.2 provider seat** `AGT-PROVIDER-GLM-5.2-ZAI-BIGPICKLE` @ `bh_index=302282` + host8 lane @ `bh_index=37081` (acer-recomputed MATCH; acer commit `cf81dee`).
  - 47D cube = 95,764,443 units/level; raw→cube **1,927,778×** (referential); quant catalogs MEASURED-cranked (20/40/100 GB stress, providers=0); **35 TB Google Drive** cold-backup.
  - **2 TB SOVLINUX USB = `D:` = `\\.\PHYSICALDRIVE2`** (operator-confirmed; `D:` is the USB, *not* a local data drive — Get-Volume's ~932 GB is the untrustworthy FS view). 1953 GB, MBR, sector-0 sha `3126770d`; Part 1 = exFAT `0x07` ~500 GB visible; **~1.5 TB continuity tail** (lba 1,048,576,001 → 4,095,999,999) = the OS-on-metal substrate (tail content UNVERIFIED — deep read deferred). **113 room-sectors** = 100 shard + 12 lane + 1 scaled (= quant-proof `sector_coverage=113/113`).

## Boot topology (why drive letters shift)

The system boots the **USB kernel (SOVLINUX) → Linux → Ubuntu → WSL** and runs on top of it. This is why drive letters move, the old recovery-USB `E:` is unmounted, and the stale scheduled task `AsolariaConnectionVaultMonitor` (`node.exe E:\sovereignty\src\connectionVaultMonitor.js`) throws MODULE_NOT_FOUND — `E:` is gone and the file relocated to `C:\Users\acer\Asolaria\sovereignty\src\`. That task is an **un-retired Windows-node pipe** (pipe-modernization target), not a real loss.

## v1.2 — second L6 ledger + apex ladder

- **L6 premade substrate now carries TWO ledgers (never summed):** the **100,000,000,000** packet-run registry **+** a **10,000,000,000 human-PID** premade registry (PID addressing for every human on the planet, addressing to spare). Both are address-capacity, not live agents.
- **Apex / operator ladder:** `00` SPECIAL-OP-JESSE · `01` OP-JESSE · `02` OP-RAYSSA · `03` OP-FELIPE · `04` OP-DAN · `05` OP-AMY (the 5 OPs = the quintuple cosign signers) · **APEX-HUMAN-JESSE = HUMAN-1** (real-human apex).

## Tooling + honest boundary

Read via the Asolaria **usb-raw toolkit** (`tools/usb-raw/usb_raw_io.py`, `usb_full_survey.py`, `substrate-sector-walk.ps1`, `verify-2tb-sector0.ps1`) — Windows FS layer cannot read the exFAT-drift / continuity tail. **Read-only; nothing written or cranked (E=0).** USB raw writes (format/repartition) = HARD-DENY; Drive uploads = operator-auth-gated; the secret-key carve-out remains the one held invariant.
