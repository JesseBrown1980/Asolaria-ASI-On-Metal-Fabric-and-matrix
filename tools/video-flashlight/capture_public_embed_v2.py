#!/usr/bin/env python3
"""Second public embed acquisition seat with explicit referrer/origin handling.

YouTube error 153 means the embedded player did not receive the client identity or
HTTP referrer it requires. This runner supplies a normal public GitHub referrer,
tries youtube.com embed, youtube-nocookie embed, and the public watch page, and waits
for an attached (not necessarily initially visible) HTML video element.

No login, user cookies, private API, DRM bypass, or protected-content circumvention is
used. A successful result remains a public derivative, never the original camera raw.
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


def finite(value: float) -> bool:
    return value == value and abs(value) != float("inf")


def oembed(video_id: str) -> dict[str, Any]:
    url = (
        "https://www.youtube.com/oembed?url="
        + quote(f"https://www.youtube.com/watch?v={video_id}", safe="")
        + "&format=json"
    )
    response = requests.get(url, timeout=30, headers={"User-Agent": core.UA})
    response.raise_for_status()
    return response.json()


def video_state(page) -> dict[str, Any] | None:
    return page.evaluate(
        """
        () => {
          const v=document.querySelector('video');
          if(!v) return null;
          return {
            currentTime:v.currentTime,
            duration:v.duration,
            paused:v.paused,
            ended:v.ended,
            readyState:v.readyState,
            networkState:v.networkState,
            width:v.videoWidth,
            height:v.videoHeight,
            error:v.error ? {code:v.error.code,message:v.error.message} : null
          };
        }
        """
    )


def prepare_video(page) -> None:
    page.evaluate(
        """
        () => {
          document.documentElement.style.background='black';
          document.body.style.margin='0';
          document.body.style.overflow='hidden';
          const v=document.querySelector('video');
          if(!v) return;
          v.muted=true; v.volume=0; v.playbackRate=1; v.controls=false;
          v.style.position='fixed'; v.style.inset='0';
          v.style.width='100vw'; v.style.height='100vh';
          v.style.objectFit='contain'; v.style.background='black';
          v.style.zIndex='2147483647';
          v.play().catch(()=>{});
        }
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-duration", type=float, default=core.MAX_DURATION_S)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostics = output / "diagnostics"
    diagnostics.mkdir(exist_ok=True)
    record_dir = output / "browser-recording-v2"
    record_dir.mkdir(exist_ok=True)

    try:
        public_meta = oembed(args.video_id)
    except Exception as exc:
        public_meta = {"title": None, "author_name": None, "oembed_error": f"{type(exc).__name__}: {exc}"}

    origin = quote(REFERRER, safe="")
    candidates = [
        (
            "youtube_embed_with_referrer",
            f"https://www.youtube.com/embed/{args.video_id}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&origin={origin}",
        ),
        (
            "youtube_nocookie_embed_with_referrer",
            f"https://www.youtube-nocookie.com/embed/{args.video_id}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&origin={origin}",
        ),
        ("youtube_public_watch", f"https://www.youtube.com/watch?v={args.video_id}&autoplay=1"),
    ]

    receipt: dict[str, Any] = {
        "schema": "ASOLARIA-PUBLIC-EMBED-ACQUISITION-v2",
        "video_id": args.video_id,
        "source_url": f"https://www.youtube.com/watch?v={args.video_id}",
        "referrer": REFERRER,
        "original_camera_raw": False,
        "authenticated_session": False,
        "drm_bypass": False,
        "public_oembed": public_meta,
        "candidate_pages": [],
        "observed_media": [],
        "attempts": [],
    }

    observed_urls: list[str] = []
    browser_capture: Path | None = None
    cookies: list[dict[str, Any]] = []
    duration_s = 0.0
    lead_s = 0.0
    selected_mode = None
    selected_page_title = None
    record_started = 0.0

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
            record_video_dir=str(record_dir),
            record_video_size={"width": 1280, "height": 720},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
            },
        )
        page = context.new_page()
        page.on(
            "request",
            lambda request: observed_urls.append(request.url)
            if "videoplayback" in request.url
            else None,
        )
        record_started = time.monotonic()

        for attempt_index, (mode, url) in enumerate(candidates):
            attempt: dict[str, Any] = {"mode": mode, "url_sha256": hashlib.sha256(url.encode()).hexdigest()}
            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=90_000,
                    referer=REFERRER,
                )
                selected_page_title = page.title()
                page.screenshot(
                    path=str(diagnostics / f"embed-v2-{attempt_index}-loaded.png"),
                    full_page=True,
                )
                page.wait_for_selector("video", state="attached", timeout=45_000)
                try:
                    for label in ("Accept all", "Accept", "I agree"):
                        button = page.get_by_role("button", name=label)
                        if button.count():
                            button.first.click(timeout=2_000)
                            break
                except Exception:
                    pass
                prepare_video(page)
                deadline = time.monotonic() + 60
                last_state = None
                body_excerpt = ""
                while time.monotonic() < deadline:
                    last_state = video_state(page)
                    if last_state and last_state.get("error"):
                        break
                    if last_state and float(last_state.get("currentTime") or 0) > 0.05:
                        selected_mode = mode
                        duration_s = float(last_state.get("duration") or 0)
                        lead_s = time.monotonic() - record_started
                        break
                    body_excerpt = page.locator("body").inner_text(timeout=5_000)[:500]
                    page.wait_for_timeout(500)
                attempt["last_state"] = last_state
                attempt["body_excerpt"] = body_excerpt
                if selected_mode:
                    attempt["status"] = "PASS_PLAYBACK_STARTED"
                    receipt["candidate_pages"].append(attempt)
                    break
                attempt["status"] = "FAILED_NO_PLAYBACK"
            except Exception as exc:
                attempt["status"] = "FAILED"
                attempt["error"] = f"{type(exc).__name__}: {exc}"
                try:
                    attempt["body_excerpt"] = page.locator("body").inner_text(timeout=3_000)[:500]
                except Exception:
                    pass
            receipt["candidate_pages"].append(attempt)

        if selected_mode:
            if not finite(duration_s) or duration_s <= 0 or duration_s > args.max_duration:
                receipt["attempts"].append(
                    {"mode": selected_mode, "status": "FAILED_DURATION", "duration_s": duration_s}
                )
                selected_mode = None
            else:
                end_deadline = time.monotonic() + duration_s + 180
                last_time = -1.0
                stagnant = 0
                while time.monotonic() < end_deadline:
                    state = video_state(page)
                    if not state:
                        raise RuntimeError("public player video element disappeared")
                    if state.get("error"):
                        raise RuntimeError(f"public player error: {state['error']}")
                    current = float(state.get("currentTime") or 0)
                    if state.get("ended") or current >= duration_s - 0.15:
                        break
                    if current <= last_time + 0.005:
                        stagnant += 1
                    else:
                        stagnant = 0
                        last_time = current
                    if stagnant > 60:
                        prepare_video(page)
                        stagnant = 0
                    page.wait_for_timeout(500)
                else:
                    raise TimeoutError("public player did not reach the end of the timeline")
                receipt["attempts"].append(
                    {"mode": selected_mode, "status": "PASS_FULL_TIMELINE", "duration_s": duration_s}
                )
        cookies = context.cookies()
        video_object = page.video
        context.close()
        if video_object is not None:
            try:
                browser_capture = Path(video_object.path())
            except Exception:
                browser_capture = None
        browser.close()

    unique_urls = sorted(set(observed_urls), key=core.candidate_score, reverse=True)
    receipt["observed_media"] = [core.sanitized_media_identity(url) for url in unique_urls]
    receipt["page_title"] = selected_page_title or public_meta.get("title")
    receipt["duration_s"] = duration_s
    receipt["selected_page_mode"] = selected_mode
    receipt["capture_lead_s"] = lead_s
    receipt["guest_cookie_count"] = len(cookies)

    final_video = output / "video.mkv"
    if selected_mode and unique_urls:
        videos = [url for url in unique_urls if core.media_kind(url) == "video"]
        audios = [url for url in unique_urls if core.media_kind(url) == "audio"]
        unknown = [url for url in unique_urls if core.media_kind(url) == "unknown"]
        session = requests.Session()
        with tempfile.TemporaryDirectory(prefix="embed-v2-media-") as temp_dir:
            temp = Path(temp_dir)
            try:
                if videos:
                    video_part = temp / "video.part"
                    video_receipt = core.download_public_stream(session, videos[0], video_part, cookies)
                    audio_part = None
                    audio_receipt = None
                    if audios:
                        audio_part = temp / "audio.part"
                        audio_receipt = core.download_public_stream(session, audios[0], audio_part, cookies)
                    core.mux(video_part, audio_part, final_video)
                elif unknown:
                    media_part = temp / "muxed.part"
                    video_receipt = core.download_public_stream(session, unknown[0], media_part, cookies)
                    audio_receipt = None
                    core.mux(media_part, None, final_video)
                else:
                    raise RuntimeError("no usable public media request observed")
                if not core.has_video(final_video):
                    raise RuntimeError("public embed network result has no video stream")
                receipt["attempts"].append(
                    {
                        "mode": "public_embed_network_stream_v2",
                        "status": "PASS",
                        "video": video_receipt,
                        "audio": audio_receipt,
                    }
                )
                receipt["source_tier"] = "PUBLIC_EMBED_NETWORK_STREAM"
                receipt["status"] = "PASS"
            except Exception as exc:
                final_video.unlink(missing_ok=True)
                receipt["attempts"].append(
                    {
                        "mode": "public_embed_network_stream_v2",
                        "status": "FAILED",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    if (
        not final_video.exists()
        and selected_mode
        and browser_capture is not None
        and browser_capture.exists()
    ):
        try:
            core.trim_capture(browser_capture, lead_s, duration_s, final_video)
            if not core.has_video(final_video):
                raise RuntimeError("trimmed public playback capture has no video")
            receipt["attempts"].append(
                {
                    "mode": "public_embed_playback_capture_v2",
                    "status": "PASS",
                    "raw_recording_sha256": core.sha256_file(browser_capture),
                    "trimmed_bytes": final_video.stat().st_size,
                    "trimmed_sha256": core.sha256_file(final_video),
                }
            )
            receipt["source_tier"] = "PUBLIC_EMBED_PLAYBACK_CAPTURE"
            receipt["status"] = "PASS"
        except Exception as exc:
            receipt["attempts"].append(
                {
                    "mode": "public_embed_playback_capture_v2",
                    "status": "FAILED",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    if final_video.exists():
        probe = core.ffprobe(final_video)
        video_stream = next(
            (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"),
            {},
        )
        receipt["output_bytes"] = final_video.stat().st_size
        receipt["output_sha256"] = core.sha256_file(final_video)
        receipt["ffprobe"] = probe
        metadata = {
            "id": args.video_id,
            "title": public_meta.get("title") or selected_page_title,
            "uploader": public_meta.get("author_name"),
            "channel": public_meta.get("author_name"),
            "channel_id": None,
            "upload_date": None,
            "timestamp": None,
            "duration": duration_s or float((probe.get("format") or {}).get("duration") or 0),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": None,
            "availability": "public_embed",
            "format_id": "public-embed-v2",
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
            f"PUBLICEMBEDV2|tier={receipt['source_tier']}|duration_s={duration_s:.6f}|"
            f"bytes={final_video.stat().st_size}|sha256={core.sha256_file(final_video)}|"
            "status=PASS|json=0"
        )
        return

    receipt.setdefault("status", "HELD_PUBLIC_EMBED_UNAVAILABLE")
    (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print("PUBLICEMBEDV2|status=HELD_PUBLIC_EMBED_UNAVAILABLE|json=0")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
