#!/usr/bin/env python3
"""Fourth unauthenticated public-media acquisition seat.

The v2 diagnostics proved that waiting for and stimulating the HTML ``video`` element
can expose signed public ``videoplayback`` requests even when the visible player is a
bot-confirmation overlay. This seat does that deliberately and fetches each observed
request through the same Playwright browser context before closing it.

No account, user-cookie export, DRM bypass, private endpoint, or protected-content
circumvention is used. Any output remains a public derivative, never camera raw.
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


def public_oembed(video_id: str) -> dict[str, Any]:
    url = (
        "https://www.youtube.com/oembed?url="
        + quote(f"https://www.youtube.com/watch?v={video_id}", safe="")
        + "&format=json"
    )
    response = requests.get(url, headers={"User-Agent": core.UA}, timeout=30)
    response.raise_for_status()
    return response.json()


def probe_summary(path: Path) -> dict[str, Any]:
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


def stimulate(page) -> dict[str, Any] | None:
    try:
        page.wait_for_selector("video", state="attached", timeout=60_000)
    except Exception:
        return None
    try:
        page.locator(".ytp-large-play-button").first.click(timeout=2_000)
    except Exception:
        pass
    try:
        return page.evaluate(
            """
            () => {
              const v=document.querySelector('video');
              if(!v) return null;
              v.muted=true; v.volume=0; v.playbackRate=1;
              v.play().catch(()=>{});
              return {
                currentTime:v.currentTime, duration:v.duration,
                readyState:v.readyState, networkState:v.networkState,
                paused:v.paused,
                error:v.error ? {code:v.error.code,message:v.error.message} : null
              };
            }
            """
        )
    except Exception:
        return None


def valid_video(part: Path, minimum_duration_s: float = 5.0) -> dict[str, Any] | None:
    try:
        summary = probe_summary(part)
    except Exception:
        return None
    if not summary["has_video"] or summary["duration_s"] < minimum_duration_s:
        return None
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--observe-seconds", type=float, default=75.0)
    parser.add_argument("--max-duration", type=float, default=3_600.0)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostics = output / "diagnostics"
    diagnostics.mkdir(exist_ok=True)

    try:
        oembed = public_oembed(args.video_id)
    except Exception as exc:
        oembed = {"title": None, "author_name": None, "error": f"{type(exc).__name__}: {exc}"}

    origin = quote(REFERRER, safe="")
    candidate_pages = [
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
        "schema": "ASOLARIA-PUBLIC-MEDIA-HARVEST-v4",
        "video_id": args.video_id,
        "source_url": f"https://www.youtube.com/watch?v={args.video_id}",
        "original_camera_raw": False,
        "authenticated_session": False,
        "drm_bypass": False,
        "referrer": REFERRER,
        "public_oembed": oembed,
        "pages": [],
        "observed_media": [],
        "fetches": [],
    }

    observed: dict[str, dict[str, Any]] = {}
    final_video = output / "video.mkv"

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

        def remember(request) -> None:
            if "videoplayback" not in request.url:
                return
            try:
                headers = request.all_headers()
            except Exception:
                headers = {}
            observed.setdefault(
                request.url,
                {
                    "url": request.url,
                    "headers": headers,
                    "identity": core.sanitized_media_identity(request.url),
                },
            )

        page.on("request", remember)

        for page_index, (mode, page_url) in enumerate(candidate_pages):
            row: dict[str, Any] = {
                "mode": mode,
                "url_sha256": hashlib.sha256(page_url.encode("utf-8")).hexdigest(),
            }
            try:
                page.goto(
                    page_url,
                    wait_until="domcontentloaded",
                    timeout=90_000,
                    referer=REFERRER,
                )
                state = stimulate(page)
                deadline = time.monotonic() + args.observe_seconds
                last_state = state
                while time.monotonic() < deadline and not observed:
                    last_state = stimulate(page) or last_state
                    page.wait_for_timeout(500)
                row["last_state"] = last_state
                row["observed_count"] = len(observed)
                row["title"] = page.title()
                try:
                    row["body_excerpt"] = page.locator("body").inner_text(timeout=5_000)[:500]
                except Exception:
                    row["body_excerpt"] = None
                row["status"] = "OBSERVED"
                page.screenshot(
                    path=str(diagnostics / f"harvest-v4-{page_index}.png"),
                    full_page=True,
                )
            except Exception as exc:
                row["status"] = "FAILED"
                row["error"] = f"{type(exc).__name__}: {exc}"
            receipt["pages"].append(row)
            if observed:
                break

        candidates = sorted(
            observed.values(),
            key=lambda row: core.candidate_score(row["url"]),
            reverse=True,
        )
        receipt["observed_media"] = [row["identity"] for row in candidates]

        with tempfile.TemporaryDirectory(prefix="public-media-v4-") as temp_dir:
            temp = Path(temp_dir)
            for index, candidate in enumerate(candidates):
                attempt: dict[str, Any] = {
                    "index": index,
                    "candidate": candidate["identity"],
                }
                part = temp / f"candidate-{index}.part"
                remuxed = temp / f"candidate-{index}.mkv"
                try:
                    request_headers = {
                        key: value
                        for key, value in candidate["headers"].items()
                        if key.lower()
                        not in {
                            "host",
                            "content-length",
                            "connection",
                            "accept-encoding",
                            "cookie",
                        }
                    }
                    request_headers.update(
                        {
                            "Range": "bytes=0-",
                            "Referer": "https://www.youtube.com/",
                            "User-Agent": core.UA,
                        }
                    )
                    response = context.request.get(
                        core.clean_range_url(candidate["url"]),
                        headers=request_headers,
                        timeout=300_000,
                        fail_on_status_code=False,
                    )
                    attempt["http_status"] = response.status
                    attempt["response_headers"] = {
                        key: value
                        for key, value in response.headers.items()
                        if key.lower()
                        in {"content-type", "content-length", "content-range", "accept-ranges"}
                    }
                    if not response.ok:
                        raise RuntimeError(f"browser-context fetch returned HTTP {response.status}")
                    body = response.body()
                    if len(body) < 1024:
                        raise RuntimeError("browser-context media body is implausibly small")
                    part.write_bytes(body)
                    attempt["download_bytes"] = len(body)
                    attempt["download_sha256"] = core.sha256_file(part)
                    summary = valid_video(part)
                    if summary is None:
                        raise RuntimeError("downloaded body is not a complete timed video")
                    if summary["duration_s"] > args.max_duration:
                        raise RuntimeError("video exceeds configured duration cap")
                    remux_all(part, remuxed)
                    final_summary = valid_video(remuxed)
                    if final_summary is None:
                        raise RuntimeError("remuxed body is not a complete timed video")
                    remuxed.replace(final_video)
                    attempt["status"] = "PASS"
                    attempt["output"] = final_summary
                    receipt["fetches"].append(attempt)
                    break
                except Exception as exc:
                    attempt["status"] = "FAILED"
                    attempt["error"] = f"{type(exc).__name__}: {exc}"
                    receipt["fetches"].append(attempt)
        context.close()
        browser.close()

    if final_video.exists():
        summary = probe_summary(final_video)
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
            "title": oembed.get("title"),
            "uploader": oembed.get("author_name"),
            "channel": oembed.get("author_name"),
            "channel_id": None,
            "upload_date": None,
            "timestamp": None,
            "duration": summary["duration_s"],
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": None,
            "availability": "public_guest_media_request",
            "format_id": "public-media-harvest-v4",
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
            "PUBLICMEDIAHARVESTV4|"
            f"observed={len(receipt['observed_media'])}|bytes={summary['bytes']}|"
            f"duration_s={summary['duration_s']:.6f}|sha256={summary['sha256']}|"
            "tier=PUBLIC_EMBED_NETWORK_STREAM|status=PASS|json=0"
        )
        return

    receipt["status"] = "HELD_PUBLIC_MEDIA_UNAVAILABLE"
    (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(
        f"PUBLICMEDIAHARVESTV4|observed={len(receipt['observed_media'])}|"
        "status=HELD_PUBLIC_MEDIA_UNAVAILABLE|json=0"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
