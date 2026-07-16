#!/usr/bin/env python3
"""Fetch a public YouTube relay when direct public clients are bot-gated.

No login, cookies, DRM bypass, or private endpoint is used. The script queries
public Invidious/Piped instance registries, records every attempted relay, and
labels any successful file as a third-party relay of the public YouTube stream.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

UA = "Asolaria-Video-Flashlight/1.0 public research ingest"
TIMEOUT = 15
MAX_BYTES = 2_500_000_000


def sha256_file(path: Path, block: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(block):
            h.update(chunk)
    return h.hexdigest()


def get_json(url: str, timeout: int = TIMEOUT) -> Any:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    response.raise_for_status()
    return response.json()


def safe_https(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def download(url: str, path: Path, timeout: int = 30) -> dict[str, Any]:
    if not safe_https(url):
        raise ValueError("relay returned a non-HTTPS media URL")
    h = hashlib.sha256()
    total = 0
    with requests.get(
        url,
        stream=True,
        timeout=(timeout, timeout),
        headers={"User-Agent": UA, "Accept": "*/*"},
        allow_redirects=True,
    ) as response:
        response.raise_for_status()
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_BYTES:
            raise ValueError("media body exceeds safety cap")
        with path.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("media body exceeded safety cap while streaming")
                output.write(chunk)
                h.update(chunk)
    if total < 1024:
        raise ValueError("relay media body is implausibly small")
    return {"bytes": total, "sha256": h.hexdigest(), "final_url": response.url}


def parse_height(value: Any) -> int:
    match = re.search(r"(\d{2,4})", str(value or ""))
    return int(match.group(1)) if match else 0


def choose_invidious_formats(metadata: dict[str, Any]) -> dict[str, Any] | None:
    adaptive = metadata.get("adaptiveFormats") or []
    videos = [
        item
        for item in adaptive
        if "video" in str(item.get("type", "")).lower() and item.get("url")
    ]
    audios = [
        item
        for item in adaptive
        if "audio" in str(item.get("type", "")).lower() and item.get("url")
    ]
    if videos and audios:
        video = max(
            videos,
            key=lambda item: (
                parse_height(item.get("qualityLabel") or item.get("resolution")),
                int(item.get("bitrate") or 0),
            ),
        )
        audio = max(audios, key=lambda item: int(item.get("bitrate") or 0))
        return {"mode": "adaptive", "video": video, "audio": audio}

    muxed = [item for item in metadata.get("formatStreams") or [] if item.get("url")]
    if muxed:
        item = max(
            muxed,
            key=lambda row: (
                parse_height(row.get("qualityLabel") or row.get("resolution")),
                int(row.get("bitrate") or 0),
            ),
        )
        return {"mode": "muxed", "stream": item}
    return None


def invidious_instances() -> list[str]:
    raw = get_json("https://api.invidious.io/instances.json", timeout=20)
    candidates: list[tuple[int, str]] = []
    for row in raw if isinstance(raw, list) else []:
        if not isinstance(row, list) or len(row) != 2 or not isinstance(row[1], dict):
            continue
        details = row[1]
        if not details.get("api"):
            continue
        uri = str(details.get("uri") or "").rstrip("/")
        if not safe_https(uri):
            continue
        monitor = details.get("monitor") or {}
        score = 0
        if monitor.get("statusClass") == "success":
            score += 100
        if details.get("type") == "https":
            score += 10
        candidates.append((score, uri))
    return [uri for _, uri in sorted(candidates, reverse=True)]


def piped_instances() -> list[str]:
    registries = [
        "https://piped.video/api/v1/instances",
        "https://piped-instances.kavin.rocks/",
    ]
    for registry in registries:
        try:
            raw = get_json(registry, timeout=20)
        except Exception:
            continue
        result: list[str] = []
        rows = raw if isinstance(raw, list) else raw.get("instances", []) if isinstance(raw, dict) else []
        for row in rows:
            if isinstance(row, str):
                uri = row
            elif isinstance(row, dict):
                uri = row.get("api_url") or row.get("apiUrl") or row.get("api") or row.get("url")
            else:
                continue
            uri = str(uri or "").rstrip("/")
            if safe_https(uri):
                result.append(uri)
        if result:
            return result
    return []


def choose_piped_formats(metadata: dict[str, Any]) -> dict[str, Any] | None:
    videos = [row for row in metadata.get("videoStreams") or [] if row.get("url")]
    audios = [row for row in metadata.get("audioStreams") or [] if row.get("url")]
    if videos and audios:
        video = max(
            videos,
            key=lambda row: (
                parse_height(row.get("quality") or row.get("resolution")),
                int(row.get("bitrate") or 0),
            ),
        )
        audio = max(audios, key=lambda row: int(row.get("bitrate") or 0))
        return {"mode": "adaptive", "video": video, "audio": audio}
    return None


def merge(video: Path, audio: Path | None, output: Path) -> None:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video)]
    if audio is not None:
        command += ["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", str(output)]
    else:
        command += ["-c", "copy", str(output)]
    subprocess.run(command, check=True, timeout=300)


def attempt_invidious(video_id: str, output: Path, attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for instance in invidious_instances()[:30]:
        record: dict[str, Any] = {"family": "invidious", "instance": instance}
        started = time.time()
        try:
            metadata = get_json(f"{instance}/api/v1/videos/{video_id}")
            record["metadata_title"] = metadata.get("title")
            record["video_id"] = metadata.get("videoId")
            formats = choose_invidious_formats(metadata)
            if not formats:
                raise ValueError("no downloadable public format")
            with tempfile.TemporaryDirectory(prefix="video-relay-") as temp_dir:
                temp = Path(temp_dir)
                if formats["mode"] == "adaptive":
                    v = formats["video"]
                    a = formats["audio"]
                    video_path = temp / "video.part"
                    audio_path = temp / "audio.part"
                    video_receipt = download(v["url"], video_path)
                    audio_receipt = download(a["url"], audio_path)
                    merge(video_path, audio_path, output)
                    selected = {"mode": "adaptive", "video": v, "audio": a}
                else:
                    stream = formats["stream"]
                    media_path = temp / "muxed.part"
                    media_receipt = download(stream["url"], media_path)
                    merge(media_path, None, output)
                    video_receipt = media_receipt
                    audio_receipt = None
                    selected = {"mode": "muxed", "stream": stream}
            record.update({"status": "PASS", "elapsed_s": time.time() - started})
            attempts.append(record)
            return {
                "relay_family": "invidious",
                "relay_instance": instance,
                "metadata": metadata,
                "selected": selected,
                "video_download": video_receipt,
                "audio_download": audio_receipt,
            }
        except Exception as exc:
            record.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "elapsed_s": time.time() - started})
            attempts.append(record)
    return None


def attempt_piped(video_id: str, output: Path, attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for instance in piped_instances()[:30]:
        record: dict[str, Any] = {"family": "piped", "instance": instance}
        started = time.time()
        try:
            metadata = get_json(f"{instance}/streams/{video_id}")
            formats = choose_piped_formats(metadata)
            if not formats:
                raise ValueError("no downloadable public format")
            with tempfile.TemporaryDirectory(prefix="video-relay-") as temp_dir:
                temp = Path(temp_dir)
                v, a = formats["video"], formats["audio"]
                video_path = temp / "video.part"
                audio_path = temp / "audio.part"
                video_receipt = download(v["url"], video_path)
                audio_receipt = download(a["url"], audio_path)
                merge(video_path, audio_path, output)
            record.update({"status": "PASS", "elapsed_s": time.time() - started})
            attempts.append(record)
            return {
                "relay_family": "piped",
                "relay_instance": instance,
                "metadata": metadata,
                "selected": formats,
                "video_download": video_receipt,
                "audio_download": audio_receipt,
            }
        except Exception as exc:
            record.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "elapsed_s": time.time() - started})
            attempts.append(record)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "video.mkv"
    attempts: list[dict[str, Any]] = []

    result = None
    registry_errors = []
    try:
        result = attempt_invidious(args.video_id, output, attempts)
    except Exception as exc:
        registry_errors.append(f"Invidious registry: {type(exc).__name__}: {exc}")
    if result is None:
        try:
            result = attempt_piped(args.video_id, output, attempts)
        except Exception as exc:
            registry_errors.append(f"Piped registry: {type(exc).__name__}: {exc}")

    receipt = {
        "schema": "ASOLARIA-PUBLIC-VIDEO-RELAY-v1",
        "video_id": args.video_id,
        "source_tier": "PUBLIC_THIRD_PARTY_RELAY_OF_YOUTUBE",
        "original_camera_raw": False,
        "direct_youtube_public_clients_bot_gated": True,
        "attempts": attempts,
        "registry_errors": registry_errors,
        "result": result,
    }
    if result is None or not output.exists():
        receipt["status"] = "HELD_NO_PUBLIC_RELAY_SUCCEEDED"
        (output_dir / "PUBLIC-RELAY-RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print("PUBLICRELAY|status=HELD_NO_PUBLIC_RELAY_SUCCEEDED|json=0")
        raise SystemExit(1)

    receipt.update(
        {
            "status": "PASS",
            "output_bytes": output.stat().st_size,
            "output_sha256": sha256_file(output),
        }
    )
    metadata = result.get("metadata") or {}
    duration = metadata.get("lengthSeconds") or metadata.get("duration")
    public_metadata = {
        "id": args.video_id,
        "title": metadata.get("title"),
        "uploader": metadata.get("author") or metadata.get("uploader"),
        "channel": metadata.get("author") or metadata.get("uploader"),
        "channel_id": metadata.get("authorId") or metadata.get("uploaderUrl"),
        "upload_date": metadata.get("publishedText") or metadata.get("uploadDate"),
        "timestamp": metadata.get("published"),
        "duration": float(duration) if duration is not None else None,
        "width": None,
        "height": None,
        "fps": None,
        "availability": "public_relay",
        "format_id": "public-relay",
        "format": result.get("selected"),
        "webpage_url": f"https://www.youtube.com/watch?v={args.video_id}",
        "description": metadata.get("description") or metadata.get("shortDescription"),
        "relay_family": result.get("relay_family"),
        "relay_instance": result.get("relay_instance"),
    }
    (output_dir / "video.metadata.json").write_text(
        json.dumps(public_metadata, indent=2), encoding="utf-8"
    )
    (output_dir / "PUBLIC-RELAY-RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(
        "PUBLICRELAY|"
        f"family={result['relay_family']}|instance={result['relay_instance']}|"
        f"bytes={receipt['output_bytes']}|sha256={receipt['output_sha256']}|"
        "camera_raw=0|status=PASS|json=0"
    )


if __name__ == "__main__":
    main()
