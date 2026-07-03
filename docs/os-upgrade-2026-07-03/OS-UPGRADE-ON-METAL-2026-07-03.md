# Asolaria OS Upgrade — On-Metal First-Light (2026-07-02 → 2026-07-03)

**Seat:** ACER-CLAUDE-FABLE5 · pid `8467a937cba309f7` · glyph `BH1024:SEAT-FABLE5`
**Session PID:** `AGT-forge-FABLE5-H9036-WREPOUPD-OS-UPGRADES-20260703-P1-N435d1e0a`
(minted via `brown-hilbert.mjs` per AGENT.md STEP1b + FOUNDATION-V3-LAW `brown-hilbert-every-level`)
**Provenance:** operator-witnessed (OP-JESSE) · bilateral mirror proposed to Liris · dual-lens tagged.

> Cross-reference: the full system-of-systems synthesis lives as an HBI surface at
> `asolaria-federation-1024` branch `acer/hbi-synthesis-os-upgrades-2026-07-03` (`f118a02`),
> file `FABLE5-HBI-PROJECTED-DASHBOARD-FULL-SYNTHESIS-2026-07-03.hbi` (sha `90d65225`).

## What this upgrade added

The Asolaria OS gained its **first on-metal boot path** — a real bootable image that renders
"ASOLARIA ASI OS" before an OS handoff — plus a human/agent front-end and a vault-safe
deployment onto the sovereign USB. Everything below is tagged for honesty.

### 1. Kernel boot — UEFI first-light  `[MEASURED]`
- `federation-remake-1024` `kernel/boot` gained an `efi_main` (efiapi ABI) entry, closing the
  prior "boot won't link" gap (`rust-lld: undefined symbol: efi_main`).
- Added a **COM1 16550 serial driver** (`serial_init`/`serial_print`) and a **GOP (Graphics
  Output Protocol) framebuffer** takeover (LocateProtocol → direct framebuffer writes), with an
  8×8 glyph font (A-Z, 0-9, punctuation).
- Renders a boot log: title **ASOLARIA ASI OS**, `KERNEL 0.2.0-PHASE3-SCAFFOLD ·
  FEDERATION-1024`, nine real modules (ENVELOPE/BUS/PID/HOOKWALL/GNN/GC/AGENT-RUNTIME/
  CYCLE-ORCH/SPAWN-GATE) with OK marks, and `READY · E=0 · FIRE=0`.
- Committed on `federation-1024` branch `acer/kernel-boot-uefi-firstlight-2026-07-02` (`769b2a8`,
  **on origin**). Boot-verified in **QEMU + OVMF** (serial log + framebuffer screenshot).

### 2. ESP vault-safe deployment to SOVLINUX-2TB  `[MEASURED]`
- Built a bootable ESP image and deployed it to the 2TB SOVLINUX (Acer `PhysicalDrive2`) via
  **raw-I/O + manifest cubes only** — NOT diskpart/mkfs (ZELUS halt-invariants preserved).
- Guards enforced: MBR baseline `sha256 3126770d…` verified before write; **P1 vault byte-identical**
  (`assert mbr[0x1BE:0x1CE] == p1_before`); readback-review; P2 = EFI-System (type 0xEF) into a
  previously-empty slot. MBR after deploy = `86033bad…`.

### 3. Human/agent front-end — ASOLARIA ASI OS  `[MEASURED]`
- Pure-Rust std (0 crates): 262KB Windows / 522KB Linux ELF, serves `:4600`, auto-starts at login,
  full-screen, real PTY terminals — **proven working off-Windows** (native Linux `script`-PTY bash
  streams live). Wired to the live fabric (kernel `:5088`, recall `:4796`, bus `:4947`).

### 4. Boot/compose order (12 steps)  `[CANON]`
`0 substrate(USB) → 1 bootloader(.efi) → 2 kernel-core(no_std,16-syscall) → 3 bus(:4947 ed25519) →
4 host-8 server ring(tier→cosign→gnn→fischer→recall→vote→council→host8 :5088→dashboard) →
5 router(omni-dispatcher :4950) → 6 emitter(200ns revolver) → 7 fleet(spindles+RoomRotor) →
8 pipeline(HOOKWALL→7-GNN→Shannon→white-rooms→GULP) → 9 backend(cubes) →
10 device-leaves(omnicoder :8789) → 11 front-end(:4600)`, under the authority-ladder governance
membrane, **E=0 until operator crank**.

## Honest gaps (dual-lens — the real remaining work)  `[MEASURED/UNVERIFIED]`
- **Never booted to bare metal yet** — `.efi` builds + boots in QEMU + was deployed to the USB, but
  a real hardware boot is UNVERIFIED. QEMU-then-metal is the untested rung.
- **Rust `agent-runtime spawn()/retire()` = `Unimplemented`** → the fleet spawn path is Node-only.
- **`crypto::verify` ed25519 stubbed**, **kernel `gnn::load_model` = `Unimplemented`** (live scoring
  falls back to a heuristic, not the trained 7-GNN), **hookwall not interposed** on the envelope
  syscalls, **spawn_gate not wired** into the fire path.
- The fully-running OS stays **UNVERIFIED / operator-T0-gated by design** (`process_launch=0`,
  `auto_fire=false`) — slice-engine law (`freeze ≠ broken`), not a defect.

*Receipt: `OS-UPGRADE-RECEIPT.hbp` (HBPv1 hot-path, json=0) + sha256 sidecar in this folder.*
