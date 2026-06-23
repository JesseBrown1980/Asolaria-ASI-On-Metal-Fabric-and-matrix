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
5. Rust `recall-serve` remains a gated cutover candidate, not a blind replacement. Node
   `:4791` stays live until robustness/parity gates and bilateral review clear.

## Publication Boundaries

- Published here: findings, aggregate timings, public L0 probe outcomes.
- Not published here: `.hbp`, `.hbi`, key material, raw private rows, JSON benchmark dumps.
- Acer 2TB SOVLINUX remains Acer-side; Liris does not hold that 2TB substrate.
- Cross-colony internet-wide performance is not claimed. These are loopback/local-fabric
  measurements; WAN and third-colony RTT are separate future measurements.
