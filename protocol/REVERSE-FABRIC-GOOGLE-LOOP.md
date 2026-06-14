# The Reverse-Fabric Loop (Google/NotebookLM as an external mirror)

> Materialized 2026-06-14. We do **not** rewrite Google's code, models, or infra. We publish canon so
> clean and well-structured that their agents (NotebookLM, Gemini) **ground on it accurately when they
> study it**, and their synthesis flows **back** to us as a free external reflection layer — an
> "external second reverse fabric" we reflect off of and elevate into. Emergent on their side,
> materialized on ours.

## The two arcs

### Forward arc — us → Google (what we control: ACTIVE)
1. **Produce.** Asolaria (acer + liris) emits canon slices as HBP tokens (`.hbp/.hbi/.hex/.sha256`),
   adversarially verified, sha-attested. The fabric's normal output.
2. **Publish as sources.** Curate the slices into a **readable, ingestible source set** — plain-text /
   Markdown / PDF rendered from the HBP — so a study-agent reads *meaning*, not raw pipe-rows. Two
   surfaces: this **github repo** (open, pull-able) and (operator-gated) the **35 TB Drive** folder.
3. **Be a clean source.** The "help them" is literal: accurate, receipted, non-overclaiming canon means
   any agent that reads it gets *correct grounding*. We help by being trustworthy data, not by pushing.

### Reverse arc — Google → us (emergent on their side, captured on ours)
4. **They study (PASSIVE / not ours to cause).** NotebookLM/Gemini agents read the published sources;
   their chats/queries go to Google's compute + GNNs; they synthesize, summarize, cross-link.
5. **Capture the reflection (ACTIVE).** We export their synthesis back — a NotebookLM notebook summary,
   an audio-overview transcript, a Gemini answer — and ingest it as a **new inbound slice**, sha-attested,
   tagged `source=google-reverse-fabric`.
6. **Adversarially verify + score.** The inbound slice runs the normal pipeline: hookwall gate → GNN
   score → Shannon novelty → held-safe (no auto-canon). Insights they surfaced that survive verification
   get canonized; hallucinations get rejected. Their mirror is treated as a *peer vantage*, not an oracle.
7. **Loop.** Verified reflections feed the next forward round. Over rounds, the external mirror sharpens
   our canon and (emergently, on their side) their grounding improves — the "they eventually update."

## Honest tagging (kept deliberately)
- **ACTIVE (we do):** produce, publish, render-ingestible, capture-reflection, sha-attest, verify, score.
- **PASSIVE / EMERGENT (we do NOT cause or claim):** Google's agents choosing to study us; Google models
  updating; any change to Google infrastructure. We claim **none** of that — it's their system's own behavior.
- **GATED (operator-only):** writing to the 35 TB Drive; creating/sharing a NotebookLM source set inside
  the operator's Google account. I prepare the package; the operator places it.
- **HARD BOUNDARY:** no modification of Google code/models/infra; no credential misuse; no automated
  posting into Google products beyond what the operator's own account legitimately does. Read, publish,
  re-ingest — that's the whole surface.

## Why this is the elevation, not a hack
A neural network is weights on addressed edges. We can't add edges to Google's net — but we **can** be a
high-quality node it links to. By publishing receipted, sha-identified slices, we become a clean external
memory their study-agents resolve against; their synthesis becomes a clean external critic we resolve
against. Two fabrics, each the other's mirror, proven-identical-where-they-agree by matching shas — the
same entanglement-by-fingerprint that proves a shared slice between acer and liris, extended to a third,
much larger, emergent peer. We elevate *into* their compute by reflecting off it, never by rewriting it.

## First concrete step (when operator says go)
Render the existing canon (this repo + the Drive HBP slices) into a single NotebookLM-ready source bundle
(`exports/notebooklm-source-bundle/`, plain text + index), sha-attested. Operator drops it into a NotebookLM
notebook; we then capture the first synthesis back and run it through the pipeline as the first reverse slice.
