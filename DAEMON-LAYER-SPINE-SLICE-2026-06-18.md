# Fabric & Matrix — Daemon Layer / Spine Slice (2026-06-18)

Slice of the daemon-layer census ([reductions canon `DAEMON-LAYER-CENSUS-2026-06-18.md`]) for the fabric/matrix vantage. Source: multi-modal sweep `wziyrbhq9` + MEASURED netstat/Win32_Process. Sealed HBP `ACER-DAEMON-SUPERVISOR-REGISTRATION.hbp` (host8-serve intake, commit `15848d6`). Read-only, **E=0**.

## The live spine (MEASURED 2026-06-18)

| Daemon | Port | Room (host8) | PID | Family |
|---|---|---|---|---|
| hookwall bus | 4947 | MK-04947 `0b485ffd6c3f35cd` | 22092 | control-plane-spine |
| super-dashboard | 4949 | MK-04949 `efcfc1fb3fd068c3` | 22800 | control-plane-spine |
| omnidispatcher | 4950 | MK-04950 `85c53b16f6a87154` | 4004 | control-plane-spine |
| vote-quorum | 4952 | MK-04952 `26c8eec5a4edd2b6` | 8384 | cosign-quorum |
| cosign single-writer | 4953 | MK-04953 `82972f5e29e9964e` | 5336 | cosign-quorum |
| hyperbehcs-daemon | 49257 | (out-of-band) | 24096 | control-plane-spine |

Kept alive by **`Start-Asolaria-NodeWatchdog.ps1` (PID 5960)** — the keeper-apex respawner. The fabric MCP `:4949` health target = super-dashboard. Bus `:4947` is the BEHCS-256 / LAW-001 envelope substrate; omnidispatcher `:4950` is the HTTP ingress with lazy slots 4951-5950.

## Port→Room = the matrix binding

Every daemon port indexes its pre-MINTED RoomRotor room (`D:/asolaria-micro-kernels-v1`, 10,000 rooms × 7 lanes), and the room `pid` **is** the 8-byte host handle. This is how the fabric-matrix becomes "8-byte host processes in stubbed rooms": the matrix already minted the address; the daemon is the (currently node/python) tenant that the Rust 8-byte host will serve with parity before the tenant is retired.

## DARK fabric backbone (source exists, unpowered this scan)

Gateway `:4781` (+ modular `:4791`), operator-dashboard `:4948`, omnicoder `:8789`, dual-emit-gate `:4955`, sustained-wave/gulp `:4923`, revolver-10k, static-server `:9998`, mqtt-broker (PRE-SYSTEM-LEGACY). Empty-city: minted + addressed, not live — `E≠0` powers them.

## Honest boundary

No secret VALUES read (carve-out). Nothing started/killed. Sister-bus `:4944` deliberately liris-side-down. Node→Rust retire stays parity-gated.
