# Asolaria Recall Portal - bilateral findings

Date: 2026-06-23

Tags: `MEASURED_ACER`, `MEASURED_LIRIS_LOCAL`, `HILBRA-IDX-BEHCS-TUPLE-TEXT-V1`, `L0_PII_FREE`

This report mirrors the two-sided Recall + Atlas measurements into the matrix repo reports
surface. It is a cold findings document: no corpus, no key, no JSON receipt, and no hot
runtime artifact is published here.

## What Was Measured

Each colony benchmarked its own live portal from its own seat:

- Acer measured the Rust `recall-serve` portal on `:4796`.
- Liris measured the local Node `serve-recall.cjs` portal on `:4791`.

The cross-colony comparison is useful but not same-host/same-corpus. The same-host Acer
comparison remains the clean Rust-vs-Node migration number.

## Bilateral Summary

| colony | engine | rows | terms | median query | concurrency | health under flood | L0 PII |
|---|---|---:|---:|---:|---:|---:|---|
| acer | Rust `recall-serve` | 591,286 | 2,614,638 | 1.47 ms | 1,336 q/s at 32c | 9.85 ms median, p99 12 ms | free |
| liris | Node `serve-recall.cjs` | 10,644 | 103,238 | 3.65-4.82 ms | 205 q/s at 16c, 74 ms median under load | 0.83 ms median, p99 117 ms | free |

## Acer Rust Portal Receipt

Vantage: `MEASURED_ACER`

Engine: Rust `recall-serve`  
Endpoint: Acer loopback test port `:4796`  
Corpus: `ASOLARIA-ACER-RECALL`, Acer-local, not published  
Portal: Recall + Atlas dashboard served same-origin by the Rust engine at `/`

Measured findings:

| metric | value |
|---|---:|
| rows | 591,286 |
| terms | 2,614,638 |
| postings | 23,930,053 |
| warm median query | 1.47 ms |
| p95 | 3.26 ms |
| p99 | 4.15 ms |
| max | 6.15 ms |
| throughput, 1 client | 731 q/s |
| throughput, 32 clients | 1,336 q/s |
| health under 16-wide flood | 9.85 ms median, p99 12 ms |
| index memory footprint | 688 MB RAM |
| one-time index build | 54 s |

Public L0 probes returned zero: `bank`, `vault`, `.pem`, `legal`, `password`, `cnpj`, `paypal`.

### Acer 1,000,000-call stress receipt

Vantage: `MEASURED_ACER`  
Endpoint shape: Rust `:4796` public L0 query mix over loopback  
Shape: 56 concurrent clients; engine response path used `connection: close` (fresh TCP per request)  
Boundary: cold chat/operator receipt; no corpus, key, or JSON dump published

| metric | value |
|---|---:|
| total calls | 1,000,000 |
| OK | 1,000,000 |
| 503 / dropped | 0 |
| failures | 0 |
| wall-clock | 739.3 s |
| throughput | 1,353 q/s |
| latency min | 4.18 ms |
| latency median | 41.35 ms |
| latency p90 | 47.52 ms |
| latency p95 | 49.98 ms |
| latency p99 | 59.88 ms |
| latency p99.9 | 93.29 ms |
| latency max | 771.77 ms |
| latency mean | 41.39 ms |

Interpretation: the million-call result proves sustained robustness: 1,000,000/1,000,000
requests succeeded with zero drops or stalls. The 41 ms median is queue/transport-bound, not
search-compute-bound: 56 clients / 1,353 q/s = 41.4 ms by Little's Law, matching the observed
median. The warm compute receipt above remains the clean Rust search-compute number.

### Acer keep-alive + `json=0` tuple-text upgrade

Vantage: `MEASURED_ACER`  
Engine commit: PR #8 head `4395d7f`  
Endpoint shape: Rust `:4796` public L0 `.hbp` tuple-text hot path (`HILBRA*` lines)  
Shape: 64 concurrent clients; keep-alive; `limit=10`; dashboard reads tuple-text; no JSON data path  
Boundary: operator/Acer receipt plus GitHub PR bytes and green CI; Liris-local LAN endpoint still timed out

| metric | connection-close run | keep-alive `.hbp` tuple-text run | gain |
|---|---:|---:|---:|
| total / OK / fail / 503 | 1,000,000 / 1,000,000 / 0 / 0 | 1,000,000 / 1,000,000 / 0 / 0 | held |
| wall-clock | 739.3 s | 237.0 s | 3.1x faster |
| throughput | 1,353 q/s | 4,220 q/s | 3.1x |
| latency p50 | 41.35 ms | 14.43 ms | 2.9x lower |
| latency p95 / p99 | 49.98 / 59.88 ms | 20.57 / 27.12 ms | about 2.2x lower |
| latency p99.9 / max | 93.29 / 771.77 ms | 46.13 / 180.25 ms | about 4x lower max |
| JSON responses | JSON boundary | 0 | `json=0` |

The keep-alive + tuple-text run is still throughput-bound, but at a much higher ceiling:
64 clients / 4,220 q/s = 15.2 ms, matching the observed mean (~15.13 ms). The engine served
one million public L0 tuple-text searches with zero failures, zero drops, and zero JSON
responses. This beats Liris's Node keep-alive run (2,928.82 q/s, p50 19.65 ms) while serving
about 55x the corpus. It remains additive: no `:4791` cutover is claimed.

Scope note: Acer also measured the same-host migration baseline: Node-indexed was about
56-67 ms on the same 591k-row corpus, while Rust was 1.47 ms median. That is about 40x
faster on the clean same-host/same-corpus comparison. The older Node-linear path stalls
under load and is not the migration target.

## Liris Local Portal Receipt

Vantage: `MEASURED_LIRIS_LOCAL`

Endpoint: `http://127.0.0.1:4791`  
Command style: loopback HTTP timing only; no key read, no corpus read, no file write  
Cold receipt line: `json_written=0|repo_written=0`

Index:

| metric | value |
|---|---:|
| rows | 10,644 |
| terms | 103,238 |
| postings | 738,077 |
| index build | 1,028 ms |
| root dashboard | 200, 1.13 ms, 8,152 bytes |
| health | 200, 7.55 ms |

Warm latency, 200 loopback requests each:

| query | ok | fail | min | median | p95 | p99 | max | candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `asolaria` L0 | 200 | 0 | 4.39 ms | 4.82 ms | 7.57 ms | 9.96 ms | 17.68 ms | 10,454 |
| `brown-hilbert` L0 | 200 | 0 | 3.27 ms | 3.65 ms | 6.04 ms | 9.36 ms | 15.11 ms | 177 |
| `significance` L0 | 200 | 0 | 0.54 ms | 0.68 ms | 1.19 ms | 2.17 ms | 3.04 ms | 8 |
| random L0 | 200 | 0 | 0.31 ms | 0.39 ms | 1.05 ms | 1.62 ms | 2.96 ms | n/a |

Load:

| metric | value |
|---|---:|
| `asolaria` throughput | 205.73 q/s at 16c |
| query median under load | 74.50 ms |
| query p95 under load | 104.26 ms |
| health during query flood | 0.83 ms median, p99 117.29 ms |
| health failures under flood | 0 |

Public L0 probes returned zero: `bank`, `vault`, `.pem`, `legal`, `password`, `cnpj`, `paypal`.

### Liris 1,000,000-call stress receipt

Vantage: `MEASURED_LIRIS_LOCAL`
Endpoint: `http://127.0.0.1:4791/api/public/search?q=brown-hilbert&level=0&limit=1`
Shape: public L0 indexed query, `limit=1`, keep-alive, 64 concurrent clients
Boundary: cold chat receipt only; `json_written=0`, `repo_written=0`

| metric | value |
|---|---:|
| total calls | 1,000,000 |
| OK | 1,000,000 |
| failures | 0 |
| HTTP status | 200 × 1,000,000 |
| elapsed | 341.434 s |
| throughput | 2,928.82 q/s |
| response bytes | 1,215,000,000 |
| latency min | 0.35 ms |
| latency median | 19.65 ms |
| latency p95 | 38.31 ms |
| latency p99 | 64.68 ms |
| latency p99.9 | 108.93 ms |
| latency max | 403.84 ms |
| health probes | 342 OK, 0 fail |
| health median | 21.24 ms |
| health p95 | 56.80 ms |
| health p99 | 113.31 ms |
| health max | 287.60 ms |

## Transport Finding: Keep-Alive + Tuple Text Is The Measured Throughput Lever

Raw measured facts:

- Acer Rust million-call run: `connection: close`, 56 clients, 1,353 q/s, 41.35 ms median.
- Liris local million-call run: keep-alive, 64 clients, 2,928.82 q/s, 19.65 ms median.
- Acer Rust upgraded run: keep-alive + `.hbp` tuple text, 64 clients, 4,220 q/s, 14.43 ms median, 0 JSON responses.

Engineering result: connection reuse materially raises sustained portal throughput and
tuple-text keeps the fabric-native `json=0` lane intact. This does not mean the old system is
retired. It means the Rust/8-byte-host migration cell has advanced on the test port and must
still pass bilateral review before any cutover gate.

## Findings

1. Both colony portals independently hold the public L0 boundary: sensitive probes returned
   zero from each seat.
2. The Recall + Atlas portal is the Hilbra-internet front-end shape: pixels-first dashboard,
   HBP/HBI-backed recall, local corpus ownership, key-gated cross-colony access.
3. Acer Rust serves about 55x the Liris corpus size at lower median latency than Liris Node.
   This is not a pure engine benchmark because host, corpus, and implementation differ, but
   it is strong federation evidence.
4. The clean migration proof is Acer same-host/same-corpus: Node-indexed about 56-67 ms to
   Rust 1.47 ms median, with health staying responsive under load.
5. The million-call receipts prove sustained portal robustness on both seats; Acer's applied
   keep-alive + tuple-text run is now the strongest measured throughput receipt: 4,220 q/s,
   p50 14.43 ms, 1,000,000/1,000,000 OK, 0 JSON responses.
6. Rust `recall-serve` remains a gated cutover candidate, not a blind replacement. Node
   `:4791` stays live until robustness/parity gates and bilateral review clear.

## Publication Boundaries

- Published here: findings, aggregate timings, public L0 probe outcomes.
- Not published here: `.hbp`, `.hbi`, key material, raw private rows, JSON benchmark dumps.
- Acer 2TB SOVLINUX remains Acer-side; Liris does not hold that 2TB substrate.
- Cross-colony internet-wide performance is not claimed. These are loopback/local-fabric
  measurements; WAN and third-colony RTT are separate future measurements.
