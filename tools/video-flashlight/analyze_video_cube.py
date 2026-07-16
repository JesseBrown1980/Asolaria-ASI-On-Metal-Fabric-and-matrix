#!/usr/bin/env python3
"""Analyze one temporal video cube and mint an exact 64→4096 feature hypercube."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

from video_features import (
    bright_components,
    canonical_json,
    ellipse_features,
    frame_statistics,
    gnn_shadow,
    line_features,
    model_tournament,
    orb_pair_geometry,
    resize_analysis,
    round_float,
    sha256_bytes,
    sha256_file,
    stable_tracks,
)
from video_hypercube import hypercube_encode


def write_contact_sheet(
    frames: list[np.ndarray], labels: list[str], path: Path, columns: int = 4
) -> None:
    if not frames:
        return
    thumbnails = []
    for frame, label in zip(frames, labels):
        image = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_AREA)
        cv2.putText(
            image,
            label,
            (8, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
        thumbnails.append(image)
    rows = math.ceil(len(thumbnails) / columns)
    blank = np.zeros_like(thumbnails[0])
    canvas = []
    for row in range(rows):
        canvas.append(
            np.hstack(
                [
                    thumbnails[row * columns + column]
                    if row * columns + column < len(thumbnails)
                    else blank
                    for column in range(columns)
                ]
            )
        )
    cv2.imwrite(
        str(path), np.vstack(canvas), [cv2.IMWRITE_JPEG_QUALITY, 88]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--source-receipt", required=True)
    parser.add_argument("--cube-id", required=True)
    parser.add_argument("--start-s", type=float, required=True)
    parser.add_argument("--end-s", type=float, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-samples", type=int, default=96)
    parser.add_argument("--passes", type=int, default=800)
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    video = Path(args.video)
    source = json.loads(Path(args.source_receipt).read_text(encoding="utf-8"))
    expected_sha = source["source_sha256"]
    actual_sha = sha256_file(video)
    if actual_sha != expected_sha:
        raise SystemExit("source SHA mismatch")

    capture = cv2.VideoCapture(str(video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if not fps or fps <= 0:
        raise SystemExit("invalid FPS")

    start_frame = max(0, int(math.floor(args.start_s * fps)))
    end_frame = min(total_frames, int(math.ceil(args.end_s * fps)))
    interval_frames = max(0, end_frame - start_frame)
    stride = max(1, math.ceil(interval_frames / max(1, args.max_samples)))
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    decoded_frame_hash = hashlib.sha256()
    frame_rows = []
    samples: list[np.ndarray] = []
    sample_labels: list[str] = []
    sample_indices: list[int] = []
    bright_nodes: list[list[dict]] = []
    ellipses: list[list[dict]] = []
    lines: list[list[dict]] = []

    frame_index = start_frame
    while frame_index < end_frame:
        ok, frame = capture.read()
        if not ok:
            break
        decoded_frame_hash.update(frame.tobytes())
        small = resize_analysis(frame)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        statistics = frame_statistics(gray)
        sampled = (
            (frame_index - start_frame) % stride == 0
            or frame_index == end_frame - 1
        )
        if sampled:
            bright = bright_components(gray)
            conics = ellipse_features(gray)
            frame_lines = line_features(gray)
        else:
            bright = []
            conics = []
            frame_lines = []
        frame_rows.append(
            {
                "frame_index": frame_index,
                "timestamp_s": frame_index / fps,
                "stats": statistics,
                "bright_count": len(bright) if sampled else None,
                "ellipse_count": len(conics) if sampled else None,
                "line_count": len(frame_lines) if sampled else None,
                "analysis_sample": sampled,
            }
        )
        if sampled:
            samples.append(gray)
            sample_labels.append(f"{frame_index / fps:.3f}s")
            sample_indices.append(frame_index)
            bright_nodes.append(bright)
            ellipses.append(conics)
            lines.append(frame_lines)
        frame_index += 1
    capture.release()

    if not frame_rows:
        raise SystemExit("no frames decoded in temporal cube")

    pair_geometry = [
        orb_pair_geometry(first, second)
        for first, second in zip(samples, samples[1:])
    ]
    tracks = stable_tracks(samples)
    models = model_tournament(pair_geometry, tracks, ellipses, bright_nodes)
    gnn = gnn_shadow(frame_rows, pair_geometry)

    feature_object = {
        "schema": "VIDEO-CUBE-CANONICAL-FEATURES-v1",
        "cube_id": args.cube_id,
        "source_sha256": actual_sha,
        "source_tier": source.get("source_tier"),
        "interval": {
            "start_s": args.start_s,
            "end_s": args.end_s,
            "start_frame": start_frame,
            "end_frame": end_frame,
        },
        "video": {"fps": fps, "width": width, "height": height},
        "frames": round_float(frame_rows),
        "sample_indices": sample_indices,
        "pair_geometry": round_float(pair_geometry),
        "track_geometry": round_float(tracks),
        "bright_nodes": round_float(bright_nodes),
        "ellipses": round_float(ellipses),
        "lines": round_float(lines),
        "models": round_float(models),
        "gnn": round_float(gnn),
    }
    feature_bytes = canonical_json(feature_object)
    hypercube, catalog, payload, _ = hypercube_encode(
        feature_bytes, args.passes
    )

    (output / "canonical-features.json").write_bytes(feature_bytes)
    (output / "hypercube-catalog.bin").write_bytes(catalog)
    (output / "hypercube-payload.zst").write_bytes(payload)
    write_contact_sheet(
        [cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) for frame in samples[:16]],
        sample_labels[:16],
        output / "contact-sheet.jpg",
    )

    leaves = {
        "source": actual_sha,
        "decoded_frames": decoded_frame_hash.hexdigest(),
        "features": sha256_bytes(feature_bytes),
        "catalog": sha256_bytes(catalog),
        "payload": sha256_bytes(payload),
        "gnn_forward": gnn.get("forward_sha256", ""),
        "gnn_reverse": gnn.get("reverse_sha256", ""),
        "models": sha256_bytes(canonical_json(round_float(models))),
    }
    omega_material = "\n".join(
        f"{key}={leaves[key]}" for key in sorted(leaves)
    ).encode("utf-8")
    omega = sha256_bytes(omega_material)

    result_body = {
        "schema": "ASOLARIA-VIDEO-FLASHLIGHT-CUBE-v1",
        "cube_id": args.cube_id,
        "status": "MEASURED_AUTOMATIC_CANDIDATE_ANALYSIS",
        "source_sha256": actual_sha,
        "source_tier": source.get("source_tier"),
        "start_s": args.start_s,
        "end_s": args.end_s,
        "frames_expected": interval_frames,
        "frames_decoded": len(frame_rows),
        "sample_frames": len(samples),
        "sample_stride": stride,
        "decoded_frame_chain_sha256": decoded_frame_hash.hexdigest(),
        "pair_geometry": round_float(pair_geometry),
        "track_summary": round_float(
            {key: value for key, value in tracks.items() if key != "measurement"}
        ),
        "models": round_float(models),
        "gnn": round_float(gnn),
        "hypercube": round_float(hypercube),
        "omega_leaves": leaves,
        "omega_cube": omega,
        "boundaries": [
            "AUTOMATIC_FEATURE_ANALYSIS_NOT_OBJECT_IDENTIFICATION",
            "PUBLIC_STREAM_NOT_CAMERA_RAW",
            "MODEL_FAMILIES_NOT_COMPARABLE_UNTIL_COMMON_HELDOUT_PIXEL_LOSS",
            "NO_ALIEN_OR_PHYSICAL_QUANTUM_CLAIM",
        ],
    }
    receipt_sha = sha256_bytes(canonical_json(result_body))
    result = {**result_body, "receipt_sha256": receipt_sha}
    (output / "CUBE-RESULT.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    (output / "CUBE-RESULT.hbp").write_text(
        "VIDEOFLASHCUBEv1"
        f"|cube={args.cube_id}|start_s={args.start_s}|end_s={args.end_s}"
        f"|frames={len(frame_rows)}|samples={len(samples)}"
        f"|floors=64,256,1024,4096|passes_per_transition={args.passes}"
        f"|restore=1|omega={omega}|receipt_sha256={receipt_sha}|json=0\n",
        encoding="utf-8",
    )

    sums = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            sums.append(f"{sha256_file(path)}  {path.name}")
    (output / "SHA256SUMS").write_text(
        "\n".join(sums) + "\n", encoding="utf-8"
    )
    print(
        "VIDEOFLASHCUBE|"
        f"cube={args.cube_id}|frames={len(frame_rows)}|samples={len(samples)}"
        f"|passes={args.passes * 3}|restore=1|omega={omega}|status=PASS|json=0"
    )


if __name__ == "__main__":
    main()
