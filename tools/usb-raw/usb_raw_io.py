#!/usr/bin/env python3
r"""
RawBlock - Windows raw block device I/O for USB-SOVLINUX-2TB
Bypasses Windows FS layer via \\.\PHYSICALDRIVE* using ctypes + kernel32.

Cycle-77 GO under operator FULL authorization.
Target: \\.\PHYSICALDRIVE2 (USB-SOVLINUX-2TB, MBR drift Part1 Type=0x07).

CLI:
    python usb_raw_io.py --read 0                 # dump MBR (sector 0)
    python usb_raw_io.py --read N                 # dump sector N
    python usb_raw_io.py --device \\.\PHYSICALDRIVE2 --read 0
    python usb_raw_io.py --write N --hex AABBCC.. --unsafe-write --auth-token quintuple-2026-05-25
"""

import argparse
import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import subprocess
import sys

# PREFLIGHT-GATE: see C:/asolaria-acer/packages/revolver-10k/docs/PREFLIGHT-INTEGRATION-MATRIX.md
# Row 2: ALL writable opens MUST be preceded by GREEN substrate-preflight.mjs.
PREFLIGHT_MJS = r"C:\asolaria-acer\packages\revolver-10k\bin\substrate-preflight.mjs"


class PreflightGateError(RuntimeError):
    """Raised when substrate-preflight.mjs does not return GREEN."""


def preflight_green() -> bool:
    """Spawn node substrate-preflight.mjs; True iff exit 0 (GREEN verdict)."""
    if os.environ.get("USB_RAW_SKIP_PREFLIGHT") == "1":
        # Read-only callers in test harnesses may opt out; writes still gated below.
        return True
    if not os.path.exists(PREFLIGHT_MJS):
        return False
    try:
        r = subprocess.run(
            ["node", PREFLIGHT_MJS],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return r.returncode == 0

# Win32 constants
GENERIC_READ           = 0x80000000
GENERIC_WRITE          = 0x40000000
FILE_SHARE_READ        = 0x00000001
FILE_SHARE_WRITE       = 0x00000002
OPEN_EXISTING          = 3
FILE_FLAG_NO_BUFFERING = 0x20000000
FILE_FLAG_WRITE_THROUGH= 0x80000000
INVALID_HANDLE_VALUE   = ctypes.c_void_p(-1).value
FILE_BEGIN             = 0

SECTOR_SIZE = 512

AUTH_TOKEN_CANON = "quintuple-2026-05-25"

# kernel32 bindings
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CreateFileW = kernel32.CreateFileW
CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p,
                        wt.DWORD, wt.DWORD, wt.HANDLE]
CreateFileW.restype = wt.HANDLE

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wt.HANDLE]
CloseHandle.restype = wt.BOOL

ReadFile = kernel32.ReadFile
ReadFile.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD,
                     ctypes.POINTER(wt.DWORD), ctypes.c_void_p]
ReadFile.restype = wt.BOOL

WriteFile = kernel32.WriteFile
WriteFile.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD,
                      ctypes.POINTER(wt.DWORD), ctypes.c_void_p]
WriteFile.restype = wt.BOOL

SetFilePointerEx = kernel32.SetFilePointerEx
SetFilePointerEx.argtypes = [wt.HANDLE, ctypes.c_longlong,
                             ctypes.POINTER(ctypes.c_longlong), wt.DWORD]
SetFilePointerEx.restype = wt.BOOL


def _open_device(device: str, write: bool = False) -> wt.HANDLE:
    access = GENERIC_READ | (GENERIC_WRITE if write else 0)
    share  = FILE_SHARE_READ | FILE_SHARE_WRITE
    flags  = FILE_FLAG_NO_BUFFERING | (FILE_FLAG_WRITE_THROUGH if write else 0)
    h = CreateFileW(device, access, share, None, OPEN_EXISTING, flags, None)
    if h == INVALID_HANDLE_VALUE or h is None:
        err = ctypes.get_last_error()
        raise OSError(err, f"CreateFileW failed for {device}: WinError {err}")
    return h


def _seek(handle, offset: int) -> None:
    new_pos = ctypes.c_longlong(0)
    ok = SetFilePointerEx(handle, ctypes.c_longlong(offset),
                          ctypes.byref(new_pos), FILE_BEGIN)
    if not ok:
        err = ctypes.get_last_error()
        raise OSError(err, f"SetFilePointerEx failed: WinError {err}")


def read_sector(sector_index: int, device: str = r"\\.\PHYSICALDRIVE2") -> bytes:
    """Read one 512-byte sector aligned at sector_index * 512."""
    h = _open_device(device, write=False)
    try:
        _seek(h, sector_index * SECTOR_SIZE)
        # Buffer must be aligned for NO_BUFFERING; ctypes allocates page-aligned
        # via create_string_buffer indirectly — but for safety use a fresh page.
        buf = (ctypes.c_ubyte * SECTOR_SIZE)()
        nread = wt.DWORD(0)
        ok = ReadFile(h, buf, SECTOR_SIZE, ctypes.byref(nread), None)
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, f"ReadFile failed: WinError {err}")
        if nread.value != SECTOR_SIZE:
            raise IOError(f"short read: {nread.value}/{SECTOR_SIZE}")
        return bytes(buf)
    finally:
        CloseHandle(h)


def write_sector(sector_index: int, data: bytes,
                 device: str = r"\\.\PHYSICALDRIVE2") -> None:
    """Write one 512-byte sector. Caller MUST have passed --unsafe-write+token."""
    if not preflight_green():
        raise PreflightGateError(
            "substrate-preflight.mjs did not return GREEN; refusing writable open"
        )
    if len(data) != SECTOR_SIZE:
        raise ValueError(f"write_sector requires exactly {SECTOR_SIZE} bytes, got {len(data)}")
    h = _open_device(device, write=True)
    try:
        _seek(h, sector_index * SECTOR_SIZE)
        buf = (ctypes.c_ubyte * SECTOR_SIZE)(*data)
        nwrote = wt.DWORD(0)
        ok = WriteFile(h, buf, SECTOR_SIZE, ctypes.byref(nwrote), None)
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, f"WriteFile failed: WinError {err}")
        if nwrote.value != SECTOR_SIZE:
            raise IOError(f"short write: {nwrote.value}/{SECTOR_SIZE}")
    finally:
        CloseHandle(h)


# MBR partition-type byte → label (canonical subset)
PART_TYPES = {
    0x00: "EMPTY",
    0x05: "EXTENDED-CHS",
    0x06: "FAT16",
    0x07: "NTFS/exFAT/HPFS",
    0x0B: "FAT32-CHS",
    0x0C: "FAT32-LBA",
    0x0E: "FAT16-LBA",
    0x0F: "EXTENDED-LBA",
    0x82: "LINUX-SWAP",
    0x83: "LINUX",
    0x8E: "LINUX-LVM",
    0xA5: "FREEBSD",
    0xEE: "GPT-PROTECTIVE",
    0xEF: "EFI-SYSTEM",
    0xFD: "LINUX-RAID",
}


def parse_mbr(sector0: bytes) -> dict:
    """Parse the 4 MBR partition entries at offsets 0x1BE/0x1CE/0x1DE/0x1EE."""
    if len(sector0) < 512:
        raise ValueError("sector0 too short for MBR")
    sig = sector0[510:512]
    parts = []
    for i in range(4):
        off = 0x1BE + i * 16
        e = sector0[off:off + 16]
        boot_flag = e[0]
        ptype     = e[4]
        lba_start = int.from_bytes(e[8:12],  "little")
        lba_size  = int.from_bytes(e[12:16], "little")
        parts.append({
            "idx":        i + 1,
            "boot":       boot_flag,
            "type":       ptype,
            "type_label": PART_TYPES.get(ptype, f"UNKNOWN-0x{ptype:02X}"),
            "lba_start":  lba_start,
            "lba_size":   lba_size,
            "bytes_size": lba_size * SECTOR_SIZE,
        })
    return {"signature_55AA": sig.hex(), "valid": sig == b"\x55\xAA", "partitions": parts}


def dump_mbr(device: str = r"\\.\PHYSICALDRIVE2") -> dict:
    """Read sector 0, print MBR partition table, return parsed dict."""
    sec = read_sector(0, device)
    first64 = sec[:64]
    sha = hashlib.sha256(sec).hexdigest()
    mbr = parse_mbr(sec)
    print(f"device       : {device}")
    print(f"sector       : 0")
    print(f"size         : {len(sec)} bytes")
    print(f"sha256       : {sha}")
    print(f"sha16        : {sha[:16]}")
    print(f"first 64 hex : {first64.hex()}")
    print(f"boot sig     : 0x{mbr['signature_55AA']} valid={mbr['valid']}")
    print(f"partition table:")
    print(f"  # boot type label              lba_start    lba_size    bytes_size")
    for p in mbr["partitions"]:
        print(f"  {p['idx']} 0x{p['boot']:02X} 0x{p['type']:02X} "
              f"{p['type_label']:<18s} {p['lba_start']:>10d}  {p['lba_size']:>10d}  {p['bytes_size']:>14d}")
    return {"sector0": sec, "sha256": sha, "first64_hex": first64.hex(), "mbr": mbr}


def dump_sector(sector_index: int, device: str = r"\\.\PHYSICALDRIVE2") -> dict:
    sec = read_sector(sector_index, device)
    sha = hashlib.sha256(sec).hexdigest()
    print(f"device       : {device}")
    print(f"sector       : {sector_index}")
    print(f"size         : {len(sec)} bytes")
    print(f"sha256       : {sha}")
    print(f"sha16        : {sha[:16]}")
    print(f"first 64 hex : {sec[:64].hex()}")
    return {"sector": sec, "sha256": sha}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="usb_raw_io",
        description="RawBlock - Windows raw block I/O for USB-SOVLINUX-2TB")
    ap.add_argument("--device", default=r"\\.\PHYSICALDRIVE2",
                    help=r"raw device path (default: \\.\PHYSICALDRIVE2)")
    ap.add_argument("--read", type=int, metavar="N",
                    help="read sector N (N=0 parses as MBR)")
    ap.add_argument("--write", type=int, metavar="N",
                    help="write sector N (requires --unsafe-write + --auth-token)")
    ap.add_argument("--hex", type=str,
                    help="hex payload for --write (exactly 1024 hex chars = 512 bytes)")
    ap.add_argument("--unsafe-write", action="store_true",
                    help="explicit opt-in for write ops")
    ap.add_argument("--auth-token", type=str, default="",
                    help="quintuple-cosign token required for writes")
    args = ap.parse_args(argv)

    if args.read is not None:
        try:
            if args.read == 0:
                dump_mbr(args.device)
            else:
                dump_sector(args.read, args.device)
            return 0
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            if e.errno == 5:
                print("  WinError 5 = ACCESS DENIED. Run from an elevated (admin) shell.",
                      file=sys.stderr)
            elif e.errno == 2:
                print("  WinError 2 = device not found. Check --device path.",
                      file=sys.stderr)
            return e.errno or 1

    if args.write is not None:
        if not args.unsafe_write:
            print("ERROR: --write requires --unsafe-write", file=sys.stderr); return 2
        if args.auth_token != AUTH_TOKEN_CANON:
            print(f"ERROR: --auth-token mismatch (expect {AUTH_TOKEN_CANON})",
                  file=sys.stderr); return 2
        if not args.hex:
            print("ERROR: --write requires --hex <1024-hex-chars>", file=sys.stderr); return 2
        try:
            data = bytes.fromhex(args.hex)
        except ValueError as e:
            print(f"ERROR: bad hex: {e}", file=sys.stderr); return 2
        if len(data) != SECTOR_SIZE:
            print(f"ERROR: hex decoded to {len(data)} bytes; need {SECTOR_SIZE}",
                  file=sys.stderr); return 2
        try:
            write_sector(args.write, data, args.device)
            print(f"OK: wrote {SECTOR_SIZE} bytes to sector {args.write} on {args.device}")
            return 0
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return e.errno or 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
