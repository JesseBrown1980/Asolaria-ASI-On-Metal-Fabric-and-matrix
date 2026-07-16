# `jmKlNBD4HGo` source-acquisition and pipeline status — 2026-07-16

## Current verdict

```text
public video identity       RESOLVED
public playable media bytes HELD
original camera raw         NOT OBTAINABLE FROM THE YOUTUBE LINK
synthetic full pipeline     PASS
operator/direct-file intake READY
```

The public oEmbed record resolves:

```text
title       Best UFO Ever Recorded!
publisher   N.E.X.U.S
video ID    jmKlNBD4HGo
```

The unauthenticated public watch page observed by the GitHub runner displayed the video identity and
approximately `19K views · 12 days ago · #uap #brazil`, but every available public player showed
`Sign in to confirm you’re not a bot`. The page supplied no playable media request to the guest
browser.

## Public acquisition attempts

Eight `yt-dlp` player-client combinations were tried without cookies or login. Every combination
returned the same bot-confirmation gate.

Public relay attempts also failed:

```text
Invidious  inv.zoomerville.com           HTTP 403
Piped      api.piped.private.coffee      HTTP 500
```

Three unauthenticated browser surfaces were then stimulated:

```text
youtube.com/embed
youtube-nocookie.com/embed
youtube.com/watch
```

All three resolved the title but remained at `currentTime=0`, exposed no `videoplayback` request, and
returned no source body. The sealed result is:

```text
HELD_PUBLIC_MEDIA_UNAVAILABLE
```

No login cookie, private endpoint, DRM bypass, or authentication circumvention was used.

## Source boundary

A YouTube page cannot provide the uploader’s original memory-card/camera file. Even when the public
stream becomes downloadable, its correct tier is a YouTube/public derivative, not camera raw.

The original source can enter only through an explicit operator/uploader file transfer with:

```text
exact file bytes
SHA-256
ffprobe receipt
optional chain-of-custody attestation
```

An attestation is recorded as an operator assertion unless independently supported; it is not silently
promoted into proof.

## Pipeline that is already green

The full mathematical-flashlight implementation has passed its synthetic end-to-end gate:

```text
decoded frames                         80 / 80
bounded geometry samples               17
candidate model families                8
hypercube floors              64, 256, 1024, 4096
refinement opportunities      800 per transition
total opportunities                    2,400
transition accepts             192, 768, 800
transition holds               608,  32,   0
feature-stream inverse                  PASS
catalog/payload SHA gates                PASS
Ω(cube)
c4337f05dfd03b2f61cc7f74bd3e6ea638b0b933e20c1a2efafe198247c68f9e
```

The synthetic candidate tournament exercised:

```text
sensor/optical artifact
planar homography
regular tetrahedron
unconstrained rigid lattice
square pyramid
triangular prism
cylindrical/planar-circle core
toroidal core
```

Candidate residuals remain `HELD_UNTIL_COMMON_HELDOUT_PIXEL_LOSS`; none are treated as object
identification.

## Real-video contract

When source bytes are supplied, the operator workflow will:

```text
1. seal exact input bytes and provenance;
2. partition the complete timeline into 27 contiguous cubes;
3. decode and scan every frame in every interval;
4. retain bounded keyframes for expensive geometry;
5. build 64→256→1024→4096 floors;
6. apply 800 deterministic opportunities to each of the three transitions;
7. run ORB, optical-flow, line, conic, bright-node, SVD/nullspace, rigidity, and model tests;
8. require exact inverse restoration for every reconstructive feature/catalog stream;
9. aggregate all 27 cube roots into Ω(video);
10. preserve all model claims as held until common held-out loss and uncertainty gates are satisfied.
```

Large media and frame bodies remain GitHub Actions artifacts. Git stores the source map, code,
provenance, hashes, and compact receipts.

## Operator intake

A separate manual workflow now accepts either:

```text
repository secret  VIDEO_MEDIA_URL
repository secret  VIDEO_MEDIA_SHA256
optional secret    VIDEO_CAMERA_RAW_ATTESTATION
```

or a direct HTTPS `media_url` plus expected SHA supplied at workflow dispatch.

The direct URL is not retained in Git; only its SHA-256 is stored. The exact media artifact is retained
for thirty days by the workflow unless repository policy changes.

## Claim boundary

No current result establishes:

```text
a tetrahedral craft
a torus or electromagnetic core
alien or extra-dimensional origin
a physical quantum process
a spacetime lattice
```

The measured achievement is the analysis/restore infrastructure. Footage-specific geometry remains
held until the exact full video is available and survives competing-model, held-out, complexity, and
reverse-readback gates.
