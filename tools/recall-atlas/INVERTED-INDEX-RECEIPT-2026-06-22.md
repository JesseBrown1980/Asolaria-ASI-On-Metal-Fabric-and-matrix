# Hilbra Recall inverted-index receipt

Date: 2026-06-22
Task: #22 — replace the synchronous O(N) Recall scan with a BEHCS tuple-text inverted index.

## What changed

`serve-recall.cjs` now builds an in-memory inverted index at startup:

- schema: `HILBRA-IDX-BEHCS-TUPLE-TEXT-V1`
- hot path: postings/intersection over tuple-text rows, not JSON scanning
- direct maps: `pid -> row`, `bh -> row`
- token postings: `term -> row refs`
- level buckets: random/search filtering does not need to scan every row
- row bodies remain in the private `.hbp` store and are only seeked for result rows

The old linear scan is still present as a debug-only fallback:

```text
ASOLARIA_RECALL_LINEAR_FALLBACK=1
```

The index can be disabled for comparison:

```text
ASOLARIA_RECALL_INVERTED_INDEX=0
```

## Liris measurement

MEASURED_LOCAL on Liris, loopback-only temporary server `127.0.0.1:4796`:

- rows: `10644`
- index enabled: `true`
- terms: `103238`
- build time: `855 ms`
- `q=readme`: `mode=inverted-index`, `count=2`, `candidate_count=41`
- `q=bank` at public L0: `count=0`, `candidate_count=2` (candidate rows existed but were filtered by level)

## Safety

- No live server was restarted.
- No corpus was published.
- No key was read or printed.
- No Host8 fire path was touched.
- Public L0 still filters by `assignLevel()` before returning a row.

## Acer next check

Run the same engine on Acer's 591,286-row corpus on a temporary loopback port first.

Expected result:

- `/api/health.search_index.enabled == true`
- `/api/health.search_index.rows == 591286`
- `q=readme` returns `mode=inverted-index`
- sensitive terms such as `bank`, `.pem`, `vault`, `legal`, `secret` return zero rows at `/api/public/search`
- p95 query time should fall below the previous synchronous full-scan behavior

Only after that should Acer restart the live `0.0.0.0:4791` engine with the new index path.
