"""yt-dlp Captions Engine (YTSage / video-lens technique)

When youtube-transcript-api hits YouTube's "Sign in to confirm you're not a
bot" wall, this engine fetches the very same caption tracks through yt-dlp,
which uses the innerTube player clients (web_embedded / mweb / android / ios)
and can borrow the user's real browser cookies — the exact combination YTSage
uses to keep working while plain transcript APIs get blocked.

Public API:
    fetch_captions_via_ytdlp(video_id, languages) -> Optional[List[dict]]
        Returns [{text, start, duration}] or None. Never raises.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.engine.youtube_transcript import get_resilient_ydl_opts

logger = logging.getLogger(__name__)

# Languages we accept when the requested ones are missing
FALLBACK_LANGS = ("en", "en-US", "en-GB", "en-orig")


def _pick_url(sub_dict: Optional[Dict[str, Any]], langs: tuple) -> Optional[Dict[str, Any]]:
    """Picks the best (ext=json3 > vtt > srt) track for the preferred language."""
    if not sub_dict:
        return None
    ext_priority = {"json3": 3, "vtt": 2, "srv3": 1, "srt": 1, "srv1": 1, "ttml": 1}

    # Exact language, then prefix match (en-US when en requested), then anything
    for lang in langs:
        tracks = sub_dict.get(lang)
        if tracks:
            return max(tracks, key=lambda t: ext_priority.get(t.get("ext"), 0))
    for lang in sorted(sub_dict.keys()):
        if any(lang.startswith(f) or f.startswith(lang) for f in FALLBACK_LANGS):
            return max(sub_dict[lang], key=lambda t: ext_priority.get(t.get("ext"), 0))
    # Last resort: first available track
    for lang in sorted(sub_dict.keys()):
        return max(sub_dict[lang], key=lambda t: ext_priority.get(t.get("ext"), 0))
    return None


def _parse_json3(data: bytes) -> List[Dict[str, Any]]:
    """Parses YouTube json3 caption events into snippet dicts."""
    out: List[Dict[str, Any]] = []
    try:
        payload = json.loads(data.decode("utf-8", errors="ignore"))
        for ev in payload.get("events", []):
            if "segs" not in ev:
                continue
            text = "".join(seg.get("utf8", "") for seg in ev["segs"]).strip()
            if not text:
                continue
            start = (ev.get("tStartMs") or 0) / 1000.0
            dur = (ev.get("dDurationMs") or 3000) / 1000.0
            out.append({"text": text, "start": round(start, 3), "duration": round(dur, 3)})
    except Exception as e:  # noqa: BLE001
        logger.debug(f"json3 parse failed: {e}")
    return out


def _parse_vtt(data: bytes) -> List[Dict[str, Any]]:
    """Minimal WebVTT cue parser (handles YouTube's inline <c> tags and dupes)."""
    import re

    out: List[Dict[str, Any]] = []
    ts = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[.,](\d{3})")
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        return out
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        m = ts.search(block)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        lines = [
            re.sub(r"<[^>]+>", "", ln).strip()
            for ln in block.splitlines()
            if "-->" not in ln and not ln.strip().startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) and ln.strip()
        ]
        body = " ".join(lines).strip()
        if not body:
            continue
        if out and out[-1]["text"] == body:          # YouTube rolling-cue dupe
            out[-1]["duration"] = round(end - out[-1]["start"], 3)
            continue
        out.append({"text": body, "start": round(start, 3), "duration": round(max(0.4, end - start), 3)})
    return out


def _snippets_from_track(track: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Downloads one caption track and parses it by extension."""
    import requests as _requests

    url = track.get("url")
    if not url:
        return []
    ext = track.get("ext", "vtt")
    try:
        resp = _requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if resp.status_code != 200:
            return []
        if ext == "json3":
            return _parse_json3(resp.content)
        return _parse_vtt(resp.content)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Caption track download failed: {e}")
        return []


def fetch_captions_via_ytdlp(
    video_id: str,
    languages: tuple = ("en", "en-US", "en-GB"),
    cookies_from_browser: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Fetches captions through yt-dlp. Returns [{text,start,duration}] or None.

    Strategy:
      1. Probe with resilient opts (web_embedded player client + cookies/proxy).
      2. If YouTube answers with the bot wall, retry borrowing cookies from the
         user's real browser (chrome → edge → firefox → brave), YTSage-style.
    """
    try:
        import yt_dlp
    except ImportError:
        return None

    base = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": list(languages) + [l for l in FALLBACK_LANGS if l not in languages],
        "socket_timeout": 12.0,
    }

    def _probe(opts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

    info: Optional[Dict[str, Any]] = None
    used_cookies_from = None
    try:
        info = _probe(get_resilient_ydl_opts(base, client_preset="web_embedded"))
    except Exception as first_err:
        msg = str(first_err).lower()
        if "sign in" in msg or "bot" in msg or "members-only" in msg or "age" in msg:
            # Bot wall — borrow a real browser session (YTSage technique)
            for browser in ("chrome", "edge", "firefox", "brave"):
                try:
                    info = _probe(get_resilient_ydl_opts(base, client_preset="mweb", cookies_from_browser=browser))
                    used_cookies_from = browser
                    break
                except Exception as be:
                    logger.debug(f"yt-dlp cookie attempt '{browser}' failed for {video_id}: {be}")
        else:
            logger.debug(f"yt-dlp captions probe failed for {video_id}: {first_err}")

    if not info:
        return None
    if used_cookies_from:
        logger.info(f"yt-dlp captions for {video_id} fetched via '{used_cookies_from}' browser cookies")

    # Manual captions are higher quality than ASR auto-captions; prefer them.
    track = _pick_url(info.get("subtitles"), tuple(languages)) \
        or _pick_url(info.get("automatic_captions"), tuple(languages))
    if not track:
        return None

    snippets = _snippets_from_track(track)
    if len(snippets) < 3:
        return None
    return snippets
