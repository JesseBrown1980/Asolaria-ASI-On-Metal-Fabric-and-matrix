# Asolaria Recall + Atlas

Publishable engine for local or colony-linked recall search.

## What Can Be Published

- `serve-recall.cjs`
- this README
- optional launch scripts

## What Must Not Be Published

- `ASOLARIA-LIRIS-RECALL.hbp`
- `ASOLARIA-LIRIS-RECALL.hbi`
- `SUMMARY-LIRIS.json` if it contains local-only operator state
- any private key file such as `C:\Users\rayss\.asolaria\recall.key`

The HBP/HBI recall corpus can contain personal, legal, financial, or customer communications.
The engine can travel between colonies; the corpus stays on the owning machine unless the
owner explicitly approves a private transfer.

## Auth Model

Loopback access is open for local browser use.
Any non-loopback caller must send HMAC link-auth headers. The shared key is never sent on
the wire.

```text
X-Asolaria-Owner-PID: OP-JESSE-PID
X-Asolaria-Colony: acer
X-Asolaria-Verb: search
X-Asolaria-Nonce: <random per-request nonce>
X-Asolaria-TS: <unix seconds>
X-Asolaria-HMAC: <lowercase hex hmac-sha256>
```

Canonical HMAC message, matching the Rust `link_auth` gate:

```text
"LINK|" + owner_pid + "|" + host + "|" + verb + "|" + nonce + "|" + ts_unix_s_be64
```

Do not put keys in URLs, headers, logs, or Git. Only the HMAC goes over the network.

The server reads the key from `ASOLARIA_RECALL_KEY` or from `ASOLARIA_RECALL_KEY_FILE`.
If neither is set, it defaults to:

```text
C:\Users\rayss\.asolaria\recall.key
```

Corpus filenames are colony-derived by default:

```text
ASOLARIA-${ASOLARIA_RECALL_COLONY}-RECALL.hbi
ASOLARIA-${ASOLARIA_RECALL_COLONY}-RECALL.hbp
SUMMARY-${ASOLARIA_RECALL_COLONY}.json
```

For Liris, the default colony remains `liris`, so the original filenames stay
`ASOLARIA-LIRIS-RECALL.*` and `SUMMARY-LIRIS.json`. A colony can override the basename with
`ASOLARIA_RECALL_BASENAME`.

## Peer Search

Set peers as a comma-separated list:

```text
ASOLARIA_RECALL_PEERS=acer=http://ACER-LAN-IP:4791,liris=http://LIRIS-LAN-IP:4791
```

Then query:

```text
GET /api/search-all?q=mcp
```

That returns the local recall result plus each configured peer result. The request to each
peer is made server-side with HMAC headers computed from the shared key.

## Access Levels

The engine mirrors Acer's Rust `level_tag` contract:

- `0` public: carve-out-clean canon/map/update rows.
- `5` federation: normal colony recall rows.
- `9` owner-private: legal, customer, financial, credential, private-device, or key-adjacent rows.

PII rules win before public-canon rules. A row matching private/legal/customer/key patterns is
owner-private even if another path fragment looks public.

The owner-private path fragments are intentionally broad. Acer's 2026-06-22 full-corpus audit
found that metadata-only rows do not reliably trigger content/long-digit checks, so path terms
such as `legal`, `bank`, `.pem`, `.key`, `vault`, `secret`, `password`, `.asolaria`, `dcim`,
`sdcard`, and `falcon-dump` are classified as owner-private. A false positive only hides a row
from public search; a false negative can leak.

Unauthenticated callers can use:

```text
GET /api/public/search?q=...
```

That route is hard-clamped to level `0`. Authenticated owner links can request deeper levels
with `level=5` or `level=9`, but the server clamps the request to the grant configured for
that owner PID.

## Browser Login

The front-end can also be opened from another trusted LAN machine, for example:

```text
http://192.168.1.10:4791/
```

Do not use `127.0.0.1` from a different computer; that points at the other computer itself.

The browser UI includes a "Remote Colony Login" panel. Paste the shared key there for the
current tab. The key is used by WebCrypto to sign the HMAC locally in the browser; the raw key
is not sent in request headers.

This is still a trusted-link design. Use TLS or a private tunnel before exposing it outside a
trusted LAN.

## Endpoints

- `/` local UI
- `/api/health` public node metadata; no row bodies
- `/api/public/search?q=...` public level-0 search only
- `/api/summary` authenticated outside loopback
- `/api/search?q=...&level=...` authenticated outside loopback
- `/api/search-all?q=...&level=...` authenticated outside loopback, queries configured peers
- `/api/seek?pid=...` or `/api/seek?bh=...` authenticated outside loopback and level-filtered
- `/api/random?level=...` authenticated outside loopback and level-filtered

## Example Launch

```powershell
$env:ASOLARIA_RECALL_BIND='0.0.0.0'
$env:ASOLARIA_RECALL_COLONY='liris'
$env:ASOLARIA_RECALL_OWNER_PID='OP-RAYSSA-PID'
$env:ASOLARIA_RECALL_ALLOWED_OWNER_PIDS='OP-JESSE-PID,OP-RAYSSA-PID'
$env:ASOLARIA_RECALL_KEY_FILE='C:\Users\rayss\.asolaria\recall.key'
node C:\tmp\asolaria-front-end\serve-recall.cjs
```
