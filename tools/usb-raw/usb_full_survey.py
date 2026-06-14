#!/usr/bin/env python3
r"""usb_full_survey.py - READ-ONLY strided full-device survey + exFAT VBR parse.

Covers the ENTIRE device at a configurable stride (default 8192 probes) so you get a
whole-device data-presence map without reading all ~4e9 sectors. NO WRITES, EVER.

  python usb_full_survey.py --device \\.\PHYSICALDRIVE2 --probes 8192
  python usb_full_survey.py --device \\.\PHYSICALDRIVE3 --probes 4096 --exfat-lba 2048

Needs an elevated/admin shell to open \\.\PHYSICALDRIVE* (WinError 5 = run elevated).
"""
import argparse, ctypes, ctypes.wintypes as wt, hashlib, struct, sys

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_FLAG_NO_BUFFERING = 0x20000000
INVALID = ctypes.c_void_p(-1).value
FILE_BEGIN = 0
SECTOR = 512
IOCTL_DISK_GET_LENGTH_INFO = 0x0007405C

k = ctypes.WinDLL("kernel32", use_last_error=True)
CreateFileW = k.CreateFileW
CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE]
CreateFileW.restype = wt.HANDLE
CloseHandle = k.CloseHandle; CloseHandle.argtypes = [wt.HANDLE]; CloseHandle.restype = wt.BOOL
ReadFile = k.ReadFile
ReadFile.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD), ctypes.c_void_p]
ReadFile.restype = wt.BOOL
SetFilePointerEx = k.SetFilePointerEx
SetFilePointerEx.argtypes = [wt.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wt.DWORD]
SetFilePointerEx.restype = wt.BOOL
DeviceIoControl = k.DeviceIoControl
DeviceIoControl.argtypes = [wt.HANDLE, wt.DWORD, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p, wt.DWORD,
                            ctypes.POINTER(wt.DWORD), ctypes.c_void_p]
DeviceIoControl.restype = wt.BOOL


def open_ro(dev):
    h = CreateFileW(dev, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                    OPEN_EXISTING, FILE_FLAG_NO_BUFFERING, None)
    if h == INVALID or h is None:
        raise OSError(ctypes.get_last_error(), f"open failed {dev}")
    return h


def dev_size(h):
    buf = ctypes.c_longlong(0); ret = wt.DWORD(0)
    if not DeviceIoControl(h, IOCTL_DISK_GET_LENGTH_INFO, None, 0, ctypes.byref(buf), 8, ctypes.byref(ret), None):
        raise OSError(ctypes.get_last_error(), "IOCTL length failed")
    return buf.value


def read_sector_at(h, byte_off):
    pos = ctypes.c_longlong(0)
    if not SetFilePointerEx(h, ctypes.c_longlong(byte_off), ctypes.byref(pos), FILE_BEGIN):
        raise OSError(ctypes.get_last_error(), "seek failed")
    buf = (ctypes.c_ubyte * SECTOR)(); n = wt.DWORD(0)
    if not ReadFile(h, buf, SECTOR, ctypes.byref(n), None):
        raise OSError(ctypes.get_last_error(), "read failed")
    return bytes(buf)[:n.value]


def parse_exfat(vbr):
    if len(vbr) < 110 or vbr[3:11] != b'EXFAT   ':
        return {"exfat": False}
    return {
        "exfat": True,
        "partition_offset": struct.unpack_from('<Q', vbr, 64)[0],
        "volume_length_sectors": struct.unpack_from('<Q', vbr, 72)[0],
        "fat_offset": struct.unpack_from('<I', vbr, 80)[0],
        "fat_length": struct.unpack_from('<I', vbr, 84)[0],
        "cluster_heap_offset": struct.unpack_from('<I', vbr, 88)[0],
        "cluster_count": struct.unpack_from('<I', vbr, 92)[0],
        "root_dir_cluster": struct.unpack_from('<I', vbr, 96)[0],
        "bytes_per_sector": 1 << vbr[108],
        "sectors_per_cluster": 1 << vbr[109],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="usb_full_survey")
    ap.add_argument("--device", default=r"\\.\PHYSICALDRIVE2")
    ap.add_argument("--probes", type=int, default=8192)
    ap.add_argument("--exfat-lba", type=int, default=2048)
    a = ap.parse_args(argv)
    h = open_ro(a.device)
    try:
        size = dev_size(h)
        total_sectors = size // SECTOR
        stride = max(1, total_sectors // a.probes)
        nonzero = zero = errs = 0
        regions = []; cur = None; probe = 0; lba = 0
        while lba < total_sectors and probe < a.probes:
            try:
                sec = read_sector_at(h, lba * SECTOR)
                isz = sec.count(0) == len(sec)
            except OSError:
                errs += 1; isz = True
            gb = lba * SECTOR / 1e9
            if isz:
                zero += 1
                if cur:
                    regions.append(cur); cur = None
            else:
                nonzero += 1
                if cur:
                    cur["end_gb"] = round(gb, 2)
                else:
                    cur = {"start_gb": round(gb, 2), "end_gb": round(gb, 2)}
            probe += 1; lba += stride
        if cur:
            regions.append(cur)
        try:
            ex = parse_exfat(read_sector_at(h, a.exfat_lba * SECTOR))
        except OSError as e:
            ex = {"exfat": False, "err": str(e)}
        print(f"device={a.device}")
        print(f"size_bytes={size} size_gb={round(size/1e9,2)} total_sectors={total_sectors}")
        print(f"probes={probe} stride_sectors={stride} stride_mb={round(stride*SECTOR/1e6,1)}")
        print(f"nonzero_probes={nonzero} zero_probes={zero} read_errors={errs}")
        print(f"exfat_vbr_lba{a.exfat_lba}={ex}")
        print("nonzero_regions_gb=" + (";".join(f"{r['start_gb']}-{r['end_gb']}" for r in regions) if regions else "NONE"))
    finally:
        CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
