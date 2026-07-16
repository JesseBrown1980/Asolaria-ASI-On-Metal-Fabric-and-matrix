#!/usr/bin/env python3
"""Verify 27 temporal cubes and build a compact Ω video super-hypercube."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from video_features import canonical_json, round_float, sha256_bytes, sha256_file
from video_hypercube import hypercube_encode


def verify_receipt(result: dict[str, Any]) -> bool:
    claimed = result.get("receipt_sha256")
    body = dict(result)
    body.pop("receipt_sha256", None)
    body.pop("artifact_path", None)
    body.pop("receipt_verified", None)
    return claimed == sha256_bytes(canonical_json(body))


def omega_gnn(cubes: list[dict[str, Any]], layers: int = 8) -> dict[str, Any]:
    embeddings = []
    for cube in cubes:
        embedding = cube.get("gnn", {}).get("embedding_mean") or []
        if len(embedding) != 10:
            embedding = [0.0] * 10
        hypercube = cube.get("hypercube", {})
        transitions = hypercube.get("transitions") or []
        accepted = sum(int(row.get("accepted", 0)) for row in transitions)
        held = sum(int(row.get("held", 0)) for row in transitions)
        embeddings.append(
            [float(value) for value in embedding]
            + [
                math.log1p(cube.get("frames_decoded", 0)) / 12,
                cube.get("sample_frames", 0) / 100,
                accepted / 2400,
                held / 2400,
            ]
        )
    initial = np.asarray(embeddings, dtype=np.float64)
    mean = initial.mean(axis=0)
    deviation = initial.std(axis=0)
    deviation[deviation < 1e-9] = 1
    initial = np.tanh((initial - mean) / deviation)

    # Temporal edges plus the two closest non-neighboring cube embeddings.
    distances = np.linalg.norm(
        initial[:, None, :] - initial[None, :, :], axis=2
    )
    neighbors: list[set[int]] = []
    for index in range(len(initial)):
        row = {candidate for candidate in (index - 1, index + 1) if 0 <= candidate < len(initial)}
        order = np.argsort(distances[index])
        for candidate in order:
            candidate = int(candidate)
            if candidate != index:
                row.add(candidate)
            if len(row) >= 4:
                break
        neighbors.append(row)

    def run(reverse: bool) -> np.ndarray:
        hidden = initial.copy()
        order = range(len(hidden) - 1, -1, -1) if reverse else range(len(hidden))
        for _ in range(layers):
            following = np.empty_like(hidden)
            for index in order:
                mean_neighbor = np.mean(
                    [hidden[candidate] for candidate in sorted(neighbors[index])],
                    axis=0,
                )
                temporal = np.zeros_like(hidden[index])
                if index > 0:
                    temporal += hidden[index - 1]
                if index + 1 < len(hidden):
                    temporal -= hidden[index + 1]
                if reverse:
                    temporal = -temporal
                following[index] = np.tanh(
                    0.55 * hidden[index] + 0.35 * mean_neighbor + 0.10 * temporal
                )
            hidden = following
        return hidden

    forward = run(False)
    reverse = run(True)
    edge_rows = [
        {"cube": cubes[index]["cube_id"], "neighbors": [cubes[item]["cube_id"] for item in sorted(row)]}
        for index, row in enumerate(neighbors)
    ]
    return {
        "schema": "VIDEO-OMEGA-GNN-SHADOW-v1",
        "status": "MEASURED_DETERMINISTIC_GNN_SHADOW_NOT_TRAINED",
        "nodes": len(cubes),
        "input_features": initial.shape[1],
        "layers": layers,
        "edges": edge_rows,
        "forward_sha256": sha256_bytes(forward.astype(">f4").tobytes()),
        "reverse_sha256": sha256_bytes(reverse.astype(">f4").tobytes()),
        "forward_reverse_mean_abs": float(np.mean(np.abs(forward - reverse))),
        "omega_embedding": [float(value) for value in ((forward + reverse) / 2).mean(axis=0)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--source-receipt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--passes", type=int, default=800)
    args = parser.parse_args()

    root = Path(args.input)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    source = json.loads(Path(args.source_receipt).read_text(encoding="utf-8"))

    cubes = []
    invalid = []
    for path in sorted(root.rglob("CUBE-RESULT.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        verified = verify_receipt(result)
        result["artifact_path"] = str(path.relative_to(root))
        result["receipt_verified"] = verified
        if not verified:
            invalid.append(result.get("cube_id", str(path)))
        cubes.append(result)
    cubes.sort(key=lambda row: (row["start_s"], row["cube_id"]))

    if len(cubes) != int(source["cube_count"]):
        invalid.append(f"cube_count={len(cubes)}")
    if any(cube.get("source_sha256") != source["source_sha256"] for cube in cubes):
        invalid.append("source_sha_mismatch")
    if any(not cube.get("hypercube", {}).get("restore") for cube in cubes):
        invalid.append("hypercube_restore_failure")

    gaps = []
    overlaps = []
    for left, right in zip(cubes, cubes[1:]):
        delta = float(right["start_s"]) - float(left["end_s"])
        if delta > 1e-6:
            gaps.append(delta)
        elif delta < -1e-6:
            overlaps.append(delta)
    if cubes:
        if abs(float(cubes[0]["start_s"]) - float(source["coverage_start_s"])) > 1e-6:
            invalid.append("coverage_start_mismatch")
        if abs(float(cubes[-1]["end_s"]) - float(source["coverage_end_s"])) > 1e-5:
            invalid.append("coverage_end_mismatch")
    if gaps:
        invalid.append(f"timeline_gaps={len(gaps)}")
    if overlaps:
        invalid.append(f"timeline_overlaps={len(overlaps)}")

    transition_totals: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"accepted": 0, "held": 0, "input_tokens": 0, "output_tokens": 0}
    )
    model_status = collections.Counter()
    model_candidates = collections.Counter()
    for cube in cubes:
        for transition in cube.get("hypercube", {}).get("transitions", []):
            row = transition_totals[transition["transition"]]
            for key in row:
                row[key] += int(transition.get(key, 0))
        for model in cube.get("models", []):
            model_status[(model["model"], model["status"])] += 1
            if model["status"] == "MEASURED_CANDIDATE":
                model_candidates[model["model"]] += 1

    gnn = omega_gnn(cubes)
    compact_cubes = []
    for cube in cubes:
        compact_cubes.append(
            {
                "cube_id": cube["cube_id"],
                "start_s": cube["start_s"],
                "end_s": cube["end_s"],
                "frames_decoded": cube["frames_decoded"],
                "sample_frames": cube["sample_frames"],
                "decoded_frame_chain_sha256": cube["decoded_frame_chain_sha256"],
                "models": cube["models"],
                "gnn": cube["gnn"],
                "hypercube": cube["hypercube"],
                "omega_cube": cube["omega_cube"],
                "receipt_sha256": cube["receipt_sha256"],
            }
        )

    super_object = {
        "schema": "ASOLARIA-VIDEO-OMEGA-CANONICAL-SUMMARY-v1",
        "video_id": source["video_id"],
        "source_sha256": source["source_sha256"],
        "source_tier": source["source_tier"],
        "duration_s": source["duration_s"],
        "cube_count": len(cubes),
        "full_timeline": not gaps and not overlaps,
        "transition_totals": dict(transition_totals),
        "model_status_counts": [
            {"model": model, "status": status, "cubes": count}
            for (model, status), count in sorted(model_status.items())
        ],
        "omega_gnn": round_float(gnn),
        "cubes": compact_cubes,
    }
    super_bytes = canonical_json(super_object)
    super_hypercube, catalog, payload, _ = hypercube_encode(super_bytes, args.passes)
    (output / "video-supercube-canonical.json").write_bytes(super_bytes)
    (output / "video-supercube-catalog.bin").write_bytes(catalog)
    (output / "video-supercube-payload.zst").write_bytes(payload)
    (output / "OMEGA-GNN.json").write_text(
        json.dumps(round_float(gnn), indent=2), encoding="utf-8"
    )

    omega_leaves = {
        "source": source["source_sha256"],
        "source_receipt": source["receipt_sha256"],
        "cubes": sha256_bytes(
            "\n".join(
                f"{cube['cube_id']}={cube['omega_cube']}" for cube in cubes
            ).encode("utf-8")
        ),
        "gnn_forward": gnn["forward_sha256"],
        "gnn_reverse": gnn["reverse_sha256"],
        "super_features": sha256_bytes(super_bytes),
        "super_catalog": sha256_bytes(catalog),
        "super_payload": sha256_bytes(payload),
    }
    omega_material = "\n".join(
        f"{key}={omega_leaves[key]}" for key in sorted(omega_leaves)
    ).encode("utf-8")
    omega_video = sha256_bytes(omega_material)

    result_body = {
        "schema": "ASOLARIA-VIDEO-OMEGA-RESULT-v1",
        "status": "PASS" if not invalid else "HELD_INVALID_RECEIPTS",
        "video_id": source["video_id"],
        "source_sha256": source["source_sha256"],
        "source_tier": source["source_tier"],
        "original_camera_raw": False,
        "cube_count": len(cubes),
        "invalid": invalid,
        "timeline_gaps": gaps,
        "timeline_overlaps": overlaps,
        "frames_decoded": sum(int(cube["frames_decoded"]) for cube in cubes),
        "sample_frames": sum(int(cube["sample_frames"]) for cube in cubes),
        "all_cube_restores": all(
            cube.get("hypercube", {}).get("restore") for cube in cubes
        ),
        "transition_totals": dict(transition_totals),
        "model_candidate_counts": dict(model_candidates),
        "model_selection": "HELD_UNTIL_COMMON_HELDOUT_PIXEL_LOSS",
        "omega_gnn": round_float(gnn),
        "super_hypercube": round_float(super_hypercube),
        "omega_leaves": omega_leaves,
        "omega_video": omega_video,
        "boundaries": [
            "PUBLIC_STREAM_NOT_CAMERA_RAW",
            "AUTOMATIC_CANDIDATE_ANALYSIS_NOT_OBJECT_IDENTIFICATION",
            "NO_TETRAHEDRON_TORUS_CRAFT_ORIGIN_OR_PHYSICAL_QUANTUM_CLAIM",
        ],
    }
    receipt_sha = sha256_bytes(canonical_json(result_body))
    result = {**result_body, "receipt_sha256": receipt_sha}
    (output / "VIDEO-OMEGA-RESULT.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    (output / "VIDEO-OMEGA-RESULT.hbp").write_text(
        "VIDEOOMEGAv1"
        f"|video_id={source['video_id']}|tier={source['source_tier']}|camera_raw=0"
        f"|cubes={len(cubes)}|frames={result_body['frames_decoded']}"
        f"|floors=64,256,1024,4096|passes_per_transition={args.passes}"
        f"|cube_restore={int(result_body['all_cube_restores'])}"
        f"|super_restore={int(super_hypercube['restore'])}"
        f"|model_selection=HELD_COMMON_PIXEL_LOSS|omega={omega_video}"
        f"|receipt_sha256={receipt_sha}|status={result_body['status']}|json=0\n",
        encoding="utf-8",
    )

    lines = [
        "# Mathematical-flashlight video result",
        "",
        f"- Video ID: `{source['video_id']}`",
        f"- Source tier: `{source['source_tier']}`",
        "- Original camera raw: **no**",
        f"- Source SHA-256: `{source['source_sha256']}`",
        f"- Temporal cubes: **{len(cubes)}**",
        f"- Decoded frames scanned: **{result_body['frames_decoded']:,}**",
        f"- Geometry sample frames: **{result_body['sample_frames']:,}**",
        f"- Cube feature restores: **{result_body['all_cube_restores']}**",
        f"- Super-hypercube restore: **{super_hypercube['restore']}**",
        f"- Ω(video): `{omega_video}`",
        "",
        "## Three 800-opportunity floor transitions",
        "",
        "| Transition | Accepted | Held | Input tokens | Output tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in sorted(transition_totals.items()):
        lines.append(
            f"| `{name}` | {row['accepted']} | {row['held']} | "
            f"{row['input_tokens']} | {row['output_tokens']} |"
        )
    lines.extend(
        [
            "",
            "## Candidate-model coverage",
            "",
        ]
    )
    for model, count in sorted(model_candidates.items()):
        lines.append(f"- `{model}` produced measurable automatic evidence in {count} cubes.")
    lines.extend(
        [
            "",
            "No cross-family winner is declared because the present residuals do not yet share one held-out pixel likelihood and complexity scale.",
            "",
            "## Boundary",
            "",
            "This result measures the downloaded public video stream, temporal features, exact feature-codebook round trips, nullspace evidence, and candidate-model diagnostics. It does not identify the object, establish a tetrahedron or torus, infer a mechanism or origin, or prove a physical quantum/spacetime model.",
            "",
        ]
    )
    (output / "VIDEO-FLASHLIGHT-RESULT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    sums = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            sums.append(f"{sha256_file(path)}  {path.name}")
    (output / "SHA256SUMS").write_text(
        "\n".join(sums) + "\n", encoding="utf-8"
    )
    print(
        "VIDEOOMEGA|"
        f"cubes={len(cubes)}|frames={result_body['frames_decoded']}"
        f"|cube_restore={int(result_body['all_cube_restores'])}"
        f"|super_restore={int(super_hypercube['restore'])}"
        f"|omega={omega_video}|status={result_body['status']}|json=0"
    )
    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
