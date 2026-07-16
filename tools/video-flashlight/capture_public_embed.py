#!/usr/bin/env python3
"""Acquire a public YouTube embed without login when API clients are bot-gated.

The preferred result is a direct public media stream URL observed by a guest Chromium
session and then downloaded byte-for-byte before expiry. If the public player can
play but its media URLs cannot be reassembled, the fallback is a full-timeline browser
playback capture. Neither result is the uploader's original camera file.

No account, exported cookies, DRM circumvention, private endpoint, or authentication
bypass is used. The receipt records every observed/requested URL by digest and strips
short-lived signatures from the public artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
MAX_DURATION_S = 3_600.0
MAX_MEDIA_BYTES = 3_000_000_000


def sha256_file(path: Path, block: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(block):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def sanitized_media_identity(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return {
        "host": parsed.netloc,
        "path": parsed.path,
        "itag": (query.get("itag") or [None])[0],
        "mime": (query.get("mime") or [None])[0],
        "clen": (query.get("clen") or [None])[0],
        "dur": (query.get("dur") or [None])[0],
        "lmt": (query.get("lmt") or [None])[0],
        "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
    }


def clean_range_url(url: str) -> str:
    parsed = urlparse(url)
    pairs = []
    for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
        if key.lower() in {"range", "rn", "rbuf"}:
            continue
        for value in values:
            pairs.append((key, value))
    return urlunparse(parsed._replace(query=urlencode(pairs)))


def media_kind(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    mime = ((query.get("mime") or [""])[0]).lower()
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    return "unknown"


def candidate_score(url: str) -> tuple[int, int, int]:
    query = parse_qs(urlparse(url).query)
    kind = media_kind(url)
    clen = int((query.get("clen") or ["0"])[0] or 0)
    itag = int((query.get("itag") or ["0"])[0] or 0)
    # Larger declared body first, then known stream type, then itag.
    return (clen, 1 if kind in {"video", "audio"} else 0, itag)


def download_public_stream(
    session: requests.Session,
    url: str,
    destination: Path,
    cookies: list[dict[str, Any]],
    timeout: int = 120,
) -> dict[str, Any]:
    for cookie in cookies:
        domain = str(cookie.get("domain") or "")
        session.cookies.set(
            str(cookie.get("name")),
            str(cookie.get("value")),
            domain=domain or None,
            path=str(cookie.get("path") or "/"),
        )
    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Referer": "https://www.youtube.com/",
        "Range": "bytes=0-",
    }
    digest = hashlib.sha256()
    total = 0
    final_url = None
    with session.get(
        clean_range_url(url),
        headers=headers,
        stream=True,
        allow_redirects=True,
        timeout=(30, timeout),
    ) as response:
        response.raise_for_status()
        final_url = response.url
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_MEDIA_BYTES:
            raise ValueError("public media stream exceeds safety cap")
        with destination.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_MEDIA_BYTES:
                    raise ValueError("public media stream exceeded safety cap")
                output.write(chunk)
                digest.update(chunk)
    if total < 1024:
        raise ValueError("public media stream was implausibly small")
    return {
        "bytes": total,
        "sha256": digest.hexdigest(),
        "final_url_sha256": hashlib.sha256(str(final_url).encode("utf-8")).hexdigest(),
    }


def ffprobe(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(path),
        ],
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout)
    return json.loads(result.stdout)


def has_video(path: Path) -> bool:
    try:
        return any(
            stream.get("codec_type") == "video"
            for stream in ffprobe(path).get("streams", [])
        )
    except Exception:
        return False


def mux(video: Path, audio: Path | None, output: Path) -> None:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video)]
    if audio is not None:
        command += ["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy"]
    else:
        command += ["-map", "0:v:0", "-c", "copy", "-an"]
    command.append(str(output))
    result = run(command, timeout=900)
    if result.returncode != 0:
        raise RuntimeError(result.stdout)


def trim_capture(raw_capture: Path, lead_s: float, duration_s: float, output: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{max(0.0, lead_s):.6f}",
        "-i",
        str(raw_capture),
        "-t",
        f"{duration_s:.6f}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    result = run(command, timeout=max(900, int(duration_s * 3)))
    if result.returncode != 0:
        raise RuntimeError(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-duration", type=float, default=MAX_DURATION_S)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostics = output / "diagnostics"
    diagnostics.mkdir(exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "ASOLARIA-PUBLIC-EMBED-ACQUISITION-v1",
        "video_id": args.video_id,
        "source_url": f"https://www.youtube.com/watch?v={args.video_id}",
        "embed_url": (
            f"https://www.youtube-nocookie.com/embed/{args.video_id}"
            "?autoplay=1&mute=1&controls=0&playsinline=1&rel=0"
        ),
        "original_camera_raw": False,
        "authenticated_session": False,
        "drm_bypass": False,
        "observed_media": [],
        "attempts": [],
    }

    record_dir = output / "browser-recording"
    record_dir.mkdir(exist_ok=True)
    browser_capture: Path | None = None
    duration_s = 0.0
    lead_s = 0.0
    observed_urls: list[str] = []
    page_title = None
    playback_started = False
    player_error = None

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
            user_agent=UA,
            record_video_dir=str(record_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.on(
            "request",
            lambda request: observed_urls.append(request.url)
            if "videoplayback" in request.url
            else None,
        )
        record_started = time.monotonic()
        try:
            page.goto(receipt["embed_url"], wait_until="domcontentloaded", timeout=90_000)
            page_title = page.title()
            page.screenshot(path=str(diagnostics / "embed-loaded.png"), full_page=True)
            try:
                page.locator("button[aria-label*='Accept']").first.click(timeout=2_000)
            except Exception:
                pass
            page.wait_for_selector("video", timeout=60_000)
            page.evaluate(
                """
                () => {
                  document.documentElement.style.background='black';
                  document.body.style.margin='0';
                  document.body.style.overflow='hidden';
                  const v=document.querySelector('video');
                  if (!v) return;
                  v.muted=true; v.volume=0; v.playbackRate=1;
                  v.style.position='fixed'; v.style.inset='0';
                  v.style.width='100vw'; v.style.height='100vh';
                  v.style.objectFit='contain'; v.style.background='black';
                  v.style.zIndex='2147483647';
                  v.controls=false;
                  v.play().catch(()=>{});
                }
                """
            )
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                state = page.evaluate(
                    """
                    () => { const v=document.querySelector('video'); return v ? {
                      currentTime:v.currentTime, duration:v.duration,
                      paused:v.paused, readyState:v.readyState,
                      error:v.error ? {code:v.error.code,message:v.error.message} : null
                    } : null; }
                    """
                )
                if state and state.get("error"):
                    player_error = state["error"]
                    break
                if state and float(state.get("currentTime") or 0) > 0.05:
                    playback_started = True
                    duration_s = float(state.get("duration") or 0)
                    lead_s = time.monotonic() - record_started
                    break
                page.wait_for_timeout(500)
            if not playback_started:
                raise RuntimeError(f"public embed did not begin playback: {player_error}")
            if not math_is_finite(duration_s) or duration_s <= 0 or duration_s > args.max_duration:
                raise ValueError(f"invalid or excessive public-player duration: {duration_s}")

            end_deadline = time.monotonic() + duration_s + 180
            last_time = -1.0
            stagnant = 0
            while time.monotonic() < end_deadline:
                state = page.evaluate(
                    """
                    () => { const v=document.querySelector('video'); return v ? {
                      currentTime:v.currentTime, duration:v.duration,
                      ended:v.ended, paused:v.paused,
                      error:v.error ? {code:v.error.code,message:v.error.message} : null
                    } : null; }
                    """
                )
                if not state:
                    raise RuntimeError("video element disappeared")
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
                    page.evaluate(
                        "() => { const v=document.querySelector('video'); if(v){v.muted=true;v.play().catch(()=>{});} }"
                    )
                    stagnant = 0
                page.wait_for_timeout(500)
            else:
                raise TimeoutError("public embed did not reach the end of the timeline")
        except Exception as exc:
            receipt["attempts"].append(
                {"mode": "public_embed_playback", "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
            )
            page.screenshot(path=str(diagnostics / "embed-failed.png"), full_page=True)
            (diagnostics / "embed-page.html").write_text(page.content(), encoding="utf-8")
        finally:
            video_object = page.video
            context.close()
            if video_object is not None:
                try:
                    browser_capture = Path(video_object.path())
                except Exception:
                    browser_capture = None
            browser.close()

    unique_urls = sorted(set(observed_urls), key=candidate_score, reverse=True)
    receipt["observed_media"] = [sanitized_media_identity(url) for url in unique_urls]
    receipt["page_title"] = page_title
    receipt["duration_s"] = duration_s
    receipt["playback_started"] = playback_started
    receipt["capture_lead_s"] = lead_s

    # Prefer harvesting the actual public media bytes observed by the guest player.
    network_output = output / "video.mkv"
    if playback_started and unique_urls:
        videos = [url for url in unique_urls if media_kind(url) == "video"]
        audios = [url for url in unique_urls if media_kind(url) == "audio"]
        unknown = [url for url in unique_urls if media_kind(url) == "unknown"]
        cookies: list[dict[str, Any]] = []
        # Guest cookies are not authentication credentials, but are not published.
        try:
            # Browser is already closed; only the collected signed media URLs are needed
            # on most public streams. Keep an empty list if no cookie snapshot is available.
            cookies = []
        except Exception:
            cookies = []
        session = requests.Session()
        with tempfile.TemporaryDirectory(prefix="embed-media-") as temp_dir:
            temp = Path(temp_dir)
            try:
                if videos:
                    video_part = temp / "video.part"
                    video_receipt = download_public_stream(session, videos[0], video_part, cookies)
                    audio_part = None
                    audio_receipt = None
                    if audios:
                        audio_part = temp / "audio.part"
                        audio_receipt = download_public_stream(session, audios[0], audio_part, cookies)
                    mux(video_part, audio_part, network_output)
                    if not has_video(network_output):
                        raise RuntimeError("muxed embed network stream has no video")
                elif unknown:
                    video_part = temp / "muxed.part"
                    video_receipt = download_public_stream(session, unknown[0], video_part, cookies)
                    audio_receipt = None
                    mux(video_part, None, network_output)
                else:
                    raise RuntimeError("no usable public media URL observed")
                receipt["attempts"].append(
                    {
                        "mode": "public_embed_network_stream",
                        "status": "PASS",
                        "video": video_receipt,
                        "audio": audio_receipt,
                    }
                )
                receipt["status"] = "PASS"
                receipt["source_tier"] = "PUBLIC_EMBED_NETWORK_STREAM"
            except Exception as exc:
                receipt["attempts"].append(
                    {"mode": "public_embed_network_stream", "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
                )
                network_output.unlink(missing_ok=True)

    # Last public fallback: full-timeline guest-browser playback capture.
    if not network_output.exists() and playback_started and browser_capture and browser_capture.exists():
        try:
            trim_capture(browser_capture, lead_s, duration_s, network_output)
            if not has_video(network_output):
                raise RuntimeError("trimmed playback capture has no video stream")
            receipt["attempts"].append(
                {
                    "mode": "public_embed_playback_capture",
                    "status": "PASS",
                    "raw_recording_sha256": sha256_file(browser_capture),
                    "trimmed_bytes": network_output.stat().st_size,
                    "trimmed_sha256": sha256_file(network_output),
                }
            )
            receipt["status"] = "PASS"
            receipt["source_tier"] = "PUBLIC_EMBED_PLAYBACK_CAPTURE"
        except Exception as exc:
            receipt["attempts"].append(
                {"mode": "public_embed_playback_capture", "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
            )

    if network_output.exists():
        probe = ffprobe(network_output)
        receipt["output_bytes"] = network_output.stat().st_size
        receipt["output_sha256"] = sha256_file(network_output)
        receipt["ffprobe"] = probe
        video_stream = next(
            (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"),
            {},
        )
        public_metadata = {
            "id": args.video_id,
            "title": page_title,
            "uploader": None,
            "channel": None,
            "channel_id": None,
            "upload_date": None,
            "timestamp": None,
            "duration": duration_s or float((probe.get("format") or {}).get("duration") or 0),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": None,
            "availability": "public_embed",
            "format_id": "public-embed",
            "format": receipt["source_tier"],
            "webpage_url": receipt["source_url"],
            "description": "",
            "embed_source_tier": receipt["source_tier"],
        }
        (output / "video.metadata.json").write_text(
            json.dumps(public_metadata, indent=2), encoding="utf-8"
        )
        (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )
        print(
            f"PUBLICEMBED|tier={receipt['source_tier']}|duration_s={duration_s:.6f}|"
            f"bytes={network_output.stat().st_size}|sha256={sha256_file(network_output)}|status=PASS|json=0"
        )
        return

    receipt.setdefault("status", "HELD_PUBLIC_EMBED_UNAVAILABLE")
    (output / "PUBLIC-EMBED-RECEIPT.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print("PUBLICEMBED|status=HELD_PUBLIC_EMBED_UNAVAILABLE|json=0")
    raise SystemExit(1)


def math_is_finite(value: float) -> bool:
    try:
        return value == value and abs(value) != float("inf")
    except Exception:
        return False


if __name__ == "__main__":
    main()
