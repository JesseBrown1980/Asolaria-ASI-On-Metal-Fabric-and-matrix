#!/usr/bin/env python3
"""Seal a downloaded public video stream and divide its full timeline into 27 cubes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fraction_to_float(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = as_float(denominator)
        return as_float(numerator) / denominator_value if denominator_value else None
    return as_float(value)


def find_video_stream(ffprobe: dict[str, Any]) -> dict[str, Any]:
    for stream in ffprobe.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--ffprobe", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--video-id", default="jmKlNBD4HGo")
    parser.add_argument("--cube-count", type=int, default=27)
    args = parser.parse_args()

    video = Path(args.video).resolve()
    metadata_path = Path(args.metadata).resolve()
    ffprobe_path = Path(args.ffprobe).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    ffprobe = json.loads(ffprobe_path.read_text(encoding="utf-8"))
    video_stream = find_video_stream(ffprobe)
    format_info = ffprobe.get("format", {})

    duration = as_float(metadata.get("duration"))
    if duration <= 0:
        duration = as_float(format_info.get("duration"))
    if duration <= 0:
        raise SystemExit("video duration unavailable")

    cube_count = args.cube_count
    if cube_count <= 0:
        raise SystemExit("cube count must be positive")

    video_sha = sha256_file(video)
    source_bytes = video.stat().st_size
    fps = fraction_to_float(video_stream.get("avg_frame_rate")) or fraction_to_float(
        video_stream.get("r_frame_rate")
    )
    estimated_frames = int(round(duration * fps)) if fps else None

    cubes: list[dict[str, Any]] = []
    for index in range(cube_count):
        start = duration * index / cube_count
        end = duration * (index + 1) / cube_count
        cubes.append(
            {
                "cube": index,
                "cube_id": f"V{index:02d}",
                "start_s": round(start, 9),
                "end_s": round(end, 9),
                "duration_s": round(end - start, 9),
                "source_sha256": video_sha,
            }
        )

    receipt = {
        "schema": "ASOLARIA-VIDEO-SOURCE-RECEIPT-v1",
        "video_id": args.video_id,
        "source_url": metadata.get("webpage_url")
        or f"https://www.youtube.com/watch?v={args.video_id}",
        "source_tier": "YOUTUBE_BEST_PUBLIC_STREAM",
        "original_camera_raw": False,
        "claim_boundary": (
            "Highest-quality stream publicly served by YouTube to the downloader; "
            "not asserted to be the uploader's original camera file."
        ),
        "downloaded_filename": video.name,
        "source_bytes": source_bytes,
        "source_sha256": video_sha,
        "title": metadata.get("title"),
        "description_sha256": hashlib.sha256(
            str(metadata.get("description") or "").encode("utf-8")
        ).hexdigest(),
        "uploader": metadata.get("uploader") or metadata.get("channel"),
        "channel_id": metadata.get("channel_id"),
        "upload_date": metadata.get("upload_date"),
        "timestamp": metadata.get("timestamp"),
        "availability": metadata.get("availability"),
        "duration_s": duration,
        "width": video_stream.get("width") or metadata.get("width"),
        "height": video_stream.get("height") or metadata.get("height"),
        "fps": fps or metadata.get("fps"),
        "estimated_decoded_frames": estimated_frames,
        "video_codec": video_stream.get("codec_name"),
        "pixel_format": video_stream.get("pix_fmt"),
        "container": format_info.get("format_name"),
        "container_duration_s": as_float(format_info.get("duration")),
        "yt_dlp_format_id": metadata.get("format_id"),
        "yt_dlp_format": metadata.get("format"),
        "cube_count": cube_count,
        "coverage_start_s": 0.0,
        "coverage_end_s": duration,
        "intentional_timeline_gaps": 0,
        "cubes": cubes,
    }
    canonical = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    receipt["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()

    (output / "SOURCE-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output / "SOURCE-RECEIPT.hbp").write_text(
        "VIDEOSOURCEv1"
        f"|video_id={args.video_id}|tier=YOUTUBE_BEST_PUBLIC_STREAM|camera_raw=0"
        f"|bytes={source_bytes}|sha256={video_sha}|duration_s={duration:.9f}"
        f"|width={receipt['width']}|height={receipt['height']}|fps={receipt['fps']}"
        f"|cubes={cube_count}|receipt_sha256={receipt['receipt_sha256']}|json=0\n",
        encoding="utf-8",
    )
    matrix = {"include": cubes}
    (output / "CHUNK-MATRIX.json").write_text(
        json.dumps(matrix, indent=2), encoding="utf-8"
    )
    (output / "CHUNK-MATRIX.compact.json").write_text(
        json.dumps(matrix, separators=(",", ":")), encoding="utf-8"
    )

    sums = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            sums.append(f"{sha256_file(path)}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(
                "matrix="
                + json.dumps(matrix, separators=(",", ":"))
                + "\n"
            )
            handle.write(f"video_sha256={video_sha}\n")
            handle.write(f"duration_s={duration:.9f}\n")
            handle.write(f"source_filename={video.name}\n")

    print(
        "VIDEOSOURCE|"
        f"video_id={args.video_id}|tier=YOUTUBE_BEST_PUBLIC_STREAM|camera_raw=0|"
        f"bytes={source_bytes}|sha256={video_sha}|duration_s={duration:.9f}|"
        f"cubes={cube_count}|coverage=FULL_TIMELINE|status=PASS|json=0"
    )


if __name__ == "__main__":
    main()
