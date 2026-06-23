# Hilbra Recall HBP tuple endpoints receipt

Date: 2026-06-22
Task: #23 — convert hot-path responses toward BEHCS/HBP tuple text without breaking existing JSON peers.

## What changed

`serve-recall.cjs` now serves additive HBP tuple-text endpoints beside the existing JSON API:

```text
/api/health.hbp
/api/public/search.hbp?q=...
/api/search.hbp?q=...&level=...
```

Existing JSON endpoints remain unchanged:

```text
/api/health
/api/public/search
/api/search
/api/search-all
```

This means Acer/Liris peer compatibility is preserved while agents can start using the `json=0` tuple-text hot path.

## Output lines

```text
HILBRAHEALTH|...|json=0
HILBRAIDX|...|json=0
HILBRAPEER|...|json=0
HILBRASEARCH|...|json=0
HILBRAMATCH|...|json=0
```

Search result rows expose metadata plus `row_sha16`; they do not inline private row bodies.

## Liris measurement

MEASURED_LOCAL on a temporary loopback-only server at `127.0.0.1:4796`:

- syntax: `node --check` passed
- rows: `10644`
- `/api/health.hbp`: emits `HILBRAHEALTH` + `HILBRAIDX`
- index schema: `HILBRA-IDX-BEHCS-TUPLE-TEXT-V1`
- `/api/public/search.hbp?q=readme&limit=2`: `mode=inverted-index`, `count=2`, `HILBRAMATCH` lines = 2
- `/api/public/search.hbp?q=bank&limit=2`: `count=0`, `candidate_count=2`
- JSON brace scan across tested HBP responses: `false`

## Safety

- No live server was restarted.
- Existing JSON peer endpoints were not removed or changed.
- No key was read or printed.
- No corpus was published.
- No Host8 fire path was touched.

## Acer next check

Run this same branch on Acer's 591,286-row corpus using a temporary loopback port and verify:

- `/api/health.hbp` reports `rows=591286`
- `/api/public/search.hbp?q=readme` returns `mode=inverted-index`
- sensitive public queries return `count=0`
- JSON peers still work on `/api/search` and `/api/search-all`

Only after that should live peer negotiation move from JSON to HBP tuple text.
