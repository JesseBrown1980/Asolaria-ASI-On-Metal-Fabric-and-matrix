# `jmKlNBD4HGo` mathematical-flashlight ingest contract

**Date:** 2026-07-16  
**Source URL:** `https://www.youtube.com/watch?v=jmKlNBD4HGo`  
**Mode:** public-stream acquisition, full-timeline chunking, model tournament, held-safe receipts

## Source boundary

A YouTube URL does not expose the original camera memory-card file. The workflow therefore uses the
highest-quality publicly served video/audio streams available to `yt-dlp`, merges them without an
additional video transcode where possible, and labels the result:

```text
SOURCE_TIER=YOUTUBE_BEST_PUBLIC_STREAM
ORIGINAL_CAMERA_RAW=0
```

It must never relabel a YouTube-derived stream as `RAW_CAMERA_ORIGINAL`. The artifact preserves the
exact downloaded bytes, SHA-256, complete `yt-dlp` metadata, format list, description, thumbnail,
subtitles when available, and `ffprobe` stream/container metadata.

## Whole-video coverage

The preparation job divides the complete decoded timeline into 27 contiguous temporal cubes. Cube
boundaries are emitted from the measured duration; there are no intentional gaps. Every cube records
its exact start/end times and source SHA.

The expensive geometry lane may select bounded keyframes inside each temporal cube, but it must also
scan every decoded frame in the interval for frame count, timing, luminance, blur, saturation, and
hash-chain measurements. A bounded analysis sample is not allowed to masquerade as whole-frame
feature extraction.

## Three hypercube transitions

Each temporal cube builds four address/codebook floors:

```text
L0  BEHCS-64
L1  BEHCS-256
L2  BEHCS-1024
L3  BEHCS-4096
```

The three transitions are:

```text
64 -> 256
256 -> 1024
1024 -> 4096
```

Each transition receives 800 deterministic refinement opportunities. Accepted and held proposals,
catalog cost, payload cost, and inverse reconstruction of the canonical feature stream are recorded.
The feature cube is a representation of measured observations; it is not claimed to reconstruct the
physical scene or the original video from its geometry features.

## Mathematical-flashlight tournament

The candidate family is intentionally plural:

```text
C0  sensor/optical artifact model
C1  planar triangle + planar circle/conic model
C2  regular tetrahedron model
C3  unconstrained tetrahedral point lattice
C4  square-pyramid model
C5  triangular-prism model
C6  cylindrical-core model
C7  toroidal-core model
```

For every candidate the pipeline records:

```text
fit-frame residual
held-out-frame residual
free-parameter count
MDL/BIC-style complexity charge
rigidity residual
camera/homography residual
nullspace/SVD evidence
unexplained residual pattern
```

A candidate may be ranked for further inspection, but no automatic output may assert a craft,
mechanism, extraterrestrial origin, spacetime grid, or physical quantum process.

## DBBH/DBWH gate

```text
candidate 3D/2D model
-> render/project forward into held-out frames
-> compare with observed pixels/features
-> reverse-estimate model state
-> require consistency within stated uncertainty
```

The gate follows the existing Asolaria restore doctrine: compact or visually persuasive output is not
accepted when the reverse path loses information. Exact byte restoration is mandatory for every
reconstructive stream and catalog claim.

## Git transport

The video and extracted frame bodies remain GitHub Actions artifacts. Git stores only code, source
identity, manifests, model definitions, hashes, and compact receipts. This respects the repository's
existing rule that Git transports the key/map/attestation rather than large bodies.
