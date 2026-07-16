#!/usr/bin/env python3
"""Acquire public media bytes observed by an unauthenticated YouTube guest page.

Some GitHub-hosted runners receive a bot-confirmation overlay even though the public
page still requests a signed ``googlevideo.com/videoplayback`` media URL. This seat
records those requests and immediately tries to download the same public bytes from
the same runner/IP before the signature expires.

No login, exported user cookie, private API, DRM bypass, or protected-content
circumvention is used. The output is a public derivative and is never labeled the
original camera memory-card file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from playwright.sync_api import sync_playwright

import capture_public_embed as core

REFERRER = "https://github.com/JesseBrown1980/Asolaria-ASI-On-Metal-Fabric-and-matrix"


def oembed(video_id: str) -> dict[str, Any]:
    url = (
        "https://www.youtube.com/oembed?url="
        + quote(f"https://www.youtube.com/watch?v={video_id}", safe="")
        + "&format=json"
    )
    response = requests.get(url, timeout=30, headers={"User-Agent": core.UA})
    response.raise_for_status()
    return response.json()


def remux_all(source: Path, destination: Path) -> None:
    result = core.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0",
            "-c",
            "copy",
            str(destination),
        ],
        timeout=900,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout)


def stream_summary(path: Path) -> dict[str, Any]:
    probe = core.ffprobe(path)
    streams = probe.get("streams", [])
    return {
        "probe": probe,
        "has_video": any(row.get("codec_type") == "video" for row in streams),
        "has_audio": any(row.get("codec_type") == "audio" for row in streams),
        "duration_s": float((probe.get("format") or {}).get("duration") or 0),
        "bytes": path.stat().st_size,
        "sha256": core.sha256_file(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--observe-seconds", type=float, default=18.0)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostics = output / "diagnostics"
    diagnostics.mkdir(exist_ok=True)

    try:
        public_meta = oembed(args.video_id)
    except Exception as exc:
        public_meta = {
            "title": None,
            "author_name": None,
            "oembed_error": f"{type(exc).__name__}: {exc}",
        }

    origin = quote(REFERRER, safe="")
    pages = [
        (
            "youtube_embed",
            f"https://www.youtube.com/embed/{args.video_id}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&origin={origin}",
        ),
        (
            "youtube_nocookie_embed",
            f"https://www.youtube-nocookie.com/embed/{args.video_id}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&origin={origin}",
        ),
        ("youtube_watch", f"https://www.youtube.com/watch?v={args.video_id}&autoplay=1"),
    ]

    receipt: dict[str, Any] = {
        "schema": "ASOLARIA-PUBLIC-MEDIA-HARVEST-v3",
        "video_id": args.video_id,
        "source_url": f"https://www.youtube.com/watch?v={args.video_id}",
        "original_camera_raw": False,
        "authenticated_session": False,
        "drm_bypass": False,
        "referrer": REFERRER,
        "public_oembed": public_meta,
        "page_attempts": [],
        "observed_media": [],
        "download_attempts": [],
    }

    observed_urls: list[str] = []
    cookies: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--autoplay-policy=no-user-gesture-required",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=core.UA,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page = context.new_page()
        page.on(
            "request",
            lambda request: observed_urls.append(request.url)
            if "videoplayback" in request.url
            else None,
        )

        for index, (mode, url) in enumerate(pages):
            row: dict[str, Any] = {
                "mode": mode,
                "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            }
            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=90_000,
                    referer=REFERRER,
                )
                try:
                    page.evaluate(
                        """
                        () => {
                          const v=document.querySelector('video');
                          if(v){v.muted=true;v.volume=0;v.play().catch(()=>{});}
                        }
                        """
                    )
                except Exception:
                    pass
                page.wait_for_timeout(max(1, int(args.observe_seconds * 1000)))
                row["title"] = page.title()
                try:
                    row["body_excerpt"] = page.locator("body").inner_text(timeout=5_000)[:500]
                except Exception:
                    row["body_excerpt"] = None
                row["media_requests_seen_total"] = len(observed_urls)
                row["status"] = "OBSERVED"
                page.screenshot(
                    path=str(diagnostics / f"harvest-{index}.png"),
                    full_page=True,
                )
            except Exception as exc:
                row["status"] = "FAILED"
                row["error"] = f"{type(exc).__name__}: {exc}"
            receipt["page_attempts"].append(row)
        cookies = context.cookies()
        context.close()
        browser.close()

    unique_urls = sorted(set(observed_urls), key=core.candidate_score, reverse=True)
    receipt["observed_media"] = [core.sanitized_media_identity(url) for url in unique_urls]
    receipt["guest_cookie_count"] = len(cookies)

    final_video = output / "video.mkv"
    session = requests.Session()
    with tempfile.TemporaryDirectory(prefix="public-media-v3-") as temp_dir:
        temp = Path(temp_dir)
        for index, url in enumerate(unique_urls):
            attempt: dict[str, Any] = {
                "candidate": core.sanitized_media_identity(url),
                "index": index,
            }
            part = temp / f"candidate-{index}.part"
            remuxed = temp / f"candidate-{index}.mkv"
            try:
                download = core.download_public_stream(
                    session,
                    url,
                    part,
                    cookies,
                    timeout=300,
                )
                attempt["download"] = download
                probe = core.ffprobe(part)
                streams = probe.get("streams", [])
                if not any(row.get("codec_type") == "video" for row in streams):
                    raise RuntimeError("candidate contains no video stream")
                remux_all(part, remuxed)
                summary = stream_summary(remuxed)
                if not summary["has_video"] or summary["duration_s"] <= 0:
                    raise RuntimeError("remuxed candidate is not a complete timed video")
                remuxed.replace(final_video)
                attempt["status"] = "PASS"
                attempt["output"] = summary
                receipt["download_attempts"].append(attempt)
                break
            except Exception as exc:
                attempt["status"] = "FAILED"
                attempt["error"] = f"{type(exc).__name__}: {exc}"
                receipt["download_attempts"].append(attempt)

    if final_video.exists():
        summary = stream_summary(final_video)
        video_stream = next(
            (
                row
                for row in summary["probe"].get("streams", [])
                if row.get("codec_type") == "video"
            ),
            {},
        )
        receipt.update(
            {
                "status": "PASS",
                "source_tier": "PUBLIC_EMBED_NETWORK_STREAM",
                "output_bytes": summary["bytes"],
                "output_sha256": summary["sha256"],
                "ffprobe": summary["probe"],
            }
        )
        metadata = {
            "id": args.video_id,
            "title": public_meta.get("title"),
            "uploader": public_meta.get("author_name"),
            "channel": public_meta.get("author_name"),
            "channel_id": None,
            "upload_date": None,
            "timestamp": None,
            "duration": summary["duration_s"],
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": None,
            "availability": "public_guest_media_request",
            "format_id": "public-media-harvest-v3",
            "format": receipt["source_tier"],
            "webpage_url": receipt["source_url"],
            "description": "",
        }
        (output / "video.metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )
        print(
            "PUBLICMEDIAHARVESTV3|"
            f"observed={len(unique_urls)}|bytes={summary['bytes']}|"
            f"duration_s={summary['duration_s']:.6f}|sha256={summary['sha256']}|"
            "tier=PUBLIC_EMBED_NETWORK_STREAM|status=PASS|json=0"
        )
        return

    receipt["status"] = "HELD_PUBLIC_MEDIA_UNAVAILABLE"
    (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(
        f"PUBLICMEDIAHARVESTV3|observed={len(unique_urls)}|"
        "status=HELD_PUBLIC_MEDIA_UNAVAILABLE|json=0"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
