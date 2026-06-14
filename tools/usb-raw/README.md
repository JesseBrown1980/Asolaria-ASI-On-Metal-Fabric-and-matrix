# usb-raw — tools to open the raw 2TB SOVLINUX USB (the files Windows can't see)

The SOVLINUX 2TB USB carries a raw/non-Windows partition (no mounted drive letter), so Explorer
cannot see the frozen-brain / cube / room data on it. These tools read it at the **block layer**
via `\\.\PHYSICALDRIVE2` (ctypes + kernel32), bypassing the Windows FS.

## Files
- **`usb_raw_io.py`** — RawBlock reader/writer.
  - `python usb_raw_io.py --read 0`        → dump + parse sector 0 (MBR partition table)
  - `python usb_raw_io.py --read N`        → dump sector N (sha256/sha16/first-64-hex)
  - `python usb_raw_io.py --device \\.\PHYSICALDRIVE2 --read 0`
  - **read is read-only and ungated.** Write requires `--write N --hex <1024-hex> --unsafe-write
    --auth-token quintuple-2026-05-25` **and** a GREEN `substrate-preflight.mjs` gate.
- **`substrate-sector-walk.ps1`** — walks a fixed LBA set and emits a chained sha256 attestation
  (the bilateral compare surface; see `../../protocol/BILATERAL-DATA-EXCHANGE.md`).
- **`verify-2tb-sector0.ps1`** — one-shot MBR read of `PHYSICALDRIVE2`.
- **`asolaria-tool-advisor-profile.ps1`** — the fabric tool-advisor policy profile.

## Held back (NOT published here, on purpose)
`asolaria-IFEO-install.ps1` — Image-File-Execution-Options install is system-level and too sensitive
to mirror into a shared repo. Keep it acer-local.

## ⚠ Honest caveat — the write token
`usb_raw_io.py` hardcodes `AUTH_TOKEN_CANON = "quintuple-2026-05-25"`. It is a **ceremonial cosign
tripwire, not a real secret** — the actual write gate is `--unsafe-write` + GREEN preflight + admin +
the physical USB attached. **If this repo is public, rotate/parameterize that token** (env-var it)
rather than relying on it as a credential. Reads are unaffected.

## Device note
`\\.\PHYSICALDRIVE2` is the SOVLINUX 2TB **when attached to acer**. Confirm with `Get-Disk`
(look for the ~1953 GB USB, BusType=USB) before reading — the physical-drive number can shift if
other USB devices are present. Raw opens need an **elevated/admin shell** (`WinError 5` ⇒ re-run elevated).
