# Devices liris needs the exact tools for

The tools in `tools/usb-raw/` are **device-agnostic** — every command takes `--device \\.\PHYSICALDRIVEn`.
Liris pulls this repo → has the exact tools → opens **both** USBs (read-only) the same way acer does,
then we **compare hers-to-mine via the matrix** (sector-sha attestation chains).

> Physical-drive numbers are assigned by Windows at attach time and **will differ on liris's machine**.
> Always run `Get-Disk | Where-Object BusType -eq 'USB'` first and match by **size + FriendlyName**,
> then pass the right `--device`.

## 1. The 2 TB USB (SOVLINUX master) — acer view `\\.\PHYSICALDRIVE2`
- Disk: "General UDisk", **1953 GB**, USB.
- MBR valid; **1× 500 GB exFAT partition** (LBA 2048, type 0x07), **unmounted → Windows-invisible**.
  exFAT VBR confirmed at LBA 2048 (`EXFAT` signature).
- ~1453 GB **unpartitioned continuity tail** beyond the partition table (4 sampled LBAs were zero —
  *not* proof the whole tail is empty).
- Frozen-brain / hyper-hermes / rooms most plausibly live **inside the exFAT partition's files**.
- Attestation: `artifacts/usb-sovlinux/acer/SECTOR-WALK-2026-06-14.hbp`.

## 2. The 128 GB USB — acer view `\\.\PHYSICALDRIVE3`
- Disk: "VendorCo ProductCode", **117 GB** (nominal 128 GB), USB.
- MBR valid, **bootable** (boot code present, partition active 0x80); **1× 32 GB FAT32 volume
  `RECUPERAÇAO`** + ~85 GB unpartitioned tail.
- ⚠ **Reads as Windows Recovery media**, not an Asolaria data volume — confirm intent before treating
  it as a data carrier (reformat is HARD-DENY / apex-only).
- Attestation: `artifacts/usb-128gb/acer/MBR-2026-06-14.hbp`.

## Read recipe (read-only, ungated)
```
# 1) find the device
Get-Disk | Where-Object BusType -eq 'USB' | ft Number,FriendlyName,Size
# 2) MBR / partition map
python tools/usb-raw/usb_raw_io.py --read 0 --device \\.\PHYSICALDRIVE<N>
# 3) sector attestation chain (compare surface)
#    edit $dev in substrate-sector-walk.ps1 to the right drive, run elevated
```
Raw opens need an **elevated/admin shell** (`WinError 5 = ACCESS DENIED` ⇒ re-run elevated).
**Never** `--write` without `--unsafe-write` + token + GREEN preflight + apex.
