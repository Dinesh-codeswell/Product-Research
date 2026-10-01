"""PulseRadar Lab API — Integrations from the OS Project Library

Consolidated router for the new capability modules:
  Wave 1:  Backups (borg), Video Reports (video-lens), FxEmbed tweet enrich (in twitter channel)
  Wave 2:  Video Frames/OCR (mcp-video-analyzer), Tool Gateway (treg)
  Wave 3:  Clip Studio (AI-Youtube-Shorts-Generator), Security Posture (shannon),
           Traffic Correlation (laravel-analytics)
  Wave 4:  Workflows (Dagu), Signals Mega-Grid (glide-data-grid),
           Browser session config (BrowserSkill)

Conventions: /api/v1 prefix, pydantic payloads, graceful degradation, no hard failures.
"""
import asyncio
import json
import logging
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger("pulseradar.lab")

router = APIRouter(prefix="/lab", tags=["Lab — OS Integrations"])

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = BACKEND_DIR / "data" / "lab_exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Optional deps — probed once at import
try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    yt_dlp = None
    HAS_YTDLP = False

try:
    import pytesseract
    pytesseract.get_tesseract_version()
    HAS_TESSERACT = True
except Exception:
    pytesseract = None
    HAS_TESSERACT = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False


# ===========================================================================
# Pydantic Schemas
# ===========================================================================

class BackupCreateRequest(BaseModel):
    name: str = Field(default="manual", description="Short label for the snapshot")
    note: str = Field(default="", description="Optional free-text note")


class ReportMarkdownRequest(BaseModel):
    title: str = "PulseRadar Report"
    subtitle: str = ""
    markdown: str


class FramesRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL or video ID")
    count: int = Field(default=6, ge=1, le=12)
    interval: Optional[int] = Field(default=None, description="Seconds between frames; auto when omitted")
    ocr: bool = True


class GatewayCallRequest(BaseModel):
    tool_id: str
    params: Dict[str, Any] = {}
    limit: int = Field(default=20, ge=1, le=100)


class ClipRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL or video ID")
    max_clips: int = Field(default=3, ge=1, le=5)
    min_duration: int = Field(default=20, ge=10, le=60)
    max_duration: int = Field(default=55, ge=15, le=90)
    # Used by /clips/cut: explicit segment bounds in seconds (override min/max semantics)
    start: Optional[float] = Field(default=None, ge=0)
    end: Optional[float] = Field(default=None, ge=0)


class WorkflowStep(BaseModel):
    name: str
    type: str = "research.run"  # research.run | seo.audit | lab.backup | webhook
    config: Dict[str, Any] = {}
    depends_on: List[str] = []


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str = ""
    steps: List[WorkflowStep]
    schedule: Optional[str] = None
    interval_hours: Optional[int] = None


class WorkflowRunBody(BaseModel):
    trigger: str = "manual"


class SecurityAuditRequest(BaseModel):
    url: str


class Ga4CorrelationRequest(BaseModel):
    domain: str
    audit_id: Optional[str] = None


class BrowserSessionConfigBody(BaseModel):
    user_data_dir: Optional[str] = None
    channels: List[str] = []


class TwitterBatchRequest(BaseModel):
    session_id: Optional[str] = None
    text: Optional[str] = None
    limit: int = Field(default=12, ge=1, le=40)


# ===========================================================================
# Wave 1 — Backups (borg-inspired snapshots)
# ===========================================================================

@router.get("/backups", summary="List backup snapshots")
async def list_backups_endpoint():
    from app.engine.backup_manager import list_backups, BACKUP_ROOT
    return {
        "backups": list_backups(),
        "backup_root": str(BACKUP_ROOT),
        "targets": ["pulseradar_db", "transcripts_cache"],
        "rotation": {"keep": 10, "policy": "newest-first; oldest removed beyond keep=10"},
    }


@router.post("/backups", summary="Create a snapshot now")
async def create_backup_endpoint(payload: BackupCreateRequest):
    from app.engine.backup_manager import create_backup, rotate_backups
    manifest = create_backup(payload.name, payload.note)
    rotate_backups(keep=10)
    return manifest


@router.delete("/backups/{snap_id}", summary="Delete a snapshot")
async def delete_backup_endpoint(snap_id: str):
    from app.engine.backup_manager import delete_backup
    if not delete_backup(snap_id):
        raise HTTPException(status_code=404, detail=f"Snapshot {snap_id} not found")
    return {"status": "deleted", "snapshot_id": snap_id}


@router.post("/backups/{snap_id}/restore", summary="Restore DB + cache from snapshot")
async def restore_backup_endpoint(snap_id: str):
    from app.engine.backup_manager import restore_backup
    result = restore_backup(snap_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Restore failed"))
    return result


@router.get("/twitter/embed", summary="FxEmbed-style media/poll data for a tweet URL")
async def twitter_embed(url: str = Query(..., description="x.com or twitter.com status URL")):
    from app.engine.twitter_embeds import fetch_embed_data
    data = await fetch_embed_data(url)
    return {"success": bool(data), "embeds": data}


@router.post("/twitter/batch", summary="Extract media/polls for many tweet URLs (research evidence enrichment)")
async def twitter_batch(payload: TwitterBatchRequest):
    """Batch FxEmbed extraction for every x.com status URL in a research session —
    used by the research page 'Extract tweet media' action and the gateway."""
    from app.engine.twitter_embeds import fetch_embed_data, TWEET_URL_REGEX
    import re as _re
    text = payload.text or ""
    urls: List[str] = []
    if payload.session_id:
        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models.entities import RawFeedback
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(RawFeedback).where(RawFeedback.session_id == payload.session_id))
            rows = res.scalars().all()
        for r in rows:
            for m in _re.finditer(TWEET_URL_REGEX, r.url or ""):
                u = m.group(0)
                if u not in urls:
                    urls.append(u)
            for m in _re.finditer(TWEET_URL_REGEX, r.content or ""):
                u = m.group(0)
                if u not in urls:
                    urls.append(u)
    else:
        for m in _re.finditer(TWEET_URL_REGEX, text):
            u = m.group(0)
            if u not in urls:
                urls.append(u)
    urls = urls[: payload.limit]

    results: List[Dict[str, Any]] = []
    for u in urls:
        embeds = await fetch_embed_data(u)
        results.append({"url": u, "embeds": embeds})
    return {
        "success": True,
        "found": len(urls),
        "enriched": sum(1 for r in results if r["embeds"]),
        "results": results,
    }


# ===========================================================================
# Wave 1 — Video Reports (video-lens-style HTML)
# ===========================================================================

@router.post("/reports/transcript/{video_id}", summary="Render video-lens HTML report for a YouTube video")
async def render_transcript_report(video_id: str):
    """Builds a standalone HTML research report (exec summary, takeaway, key points,
    timestamped outline, embedded player) from the cached/live transcript."""
    from app.engine.youtube_transcript import YouTubeTranscriptEngine, extract_video_id
    from app.engine.report_renderer import render_transcript_report_html

    clean_id = extract_video_id(video_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")
    res = YouTubeTranscriptEngine.get_transcript(url_or_id=clean_id)
    if not res.get("success") and not res.get("text"):
        raise HTTPException(status_code=400, detail=res.get("error", "No transcript available"))
    html = render_transcript_report_html(
        video_id=clean_id,
        video_title=res.get("video_title") or "Video Report",
        channel=res.get("channel"),
        duration_text=(res.get("stats") or {}).get("formatted_duration"),
        transcript_text=res.get("text") or "",
        snippets=res.get("snippets") or [],
        stats=res.get("stats"),
    )
    return HTMLResponse(content=html, media_type="text/html")


@router.post("/reports/markdown", summary="Render a markdown doc (PRD/brief) as report HTML")
async def render_markdown_report(payload: ReportMarkdownRequest):
    from app.engine.report_renderer import render_markdown_report_html
    html = render_markdown_report_html(payload.title, payload.subtitle, payload.markdown)
    return HTMLResponse(content=html, media_type="text/html")


@router.post("/diagrams/interactive", summary="Archify-style interactive diagram from markdown (pan/zoom/collapse HTML)")
async def build_interactive_diagram(payload: ReportMarkdownRequest):
    """Turns a PRD/brief into an explorable HTML mindmap — sections as branches,
    requirement bullets as leaves. Pan, zoom, collapse. Single standalone file."""
    from app.engine.diagram_builder import build_interactive_diagram_html
    html = build_interactive_diagram_html(payload.title, payload.markdown)
    return HTMLResponse(content=html, media_type="text/html")


# ===========================================================================
# Wave 2 — Video Frames + OCR (mcp-video-analyzer-inspired)
# ===========================================================================

def _probe_duration(video_path: Path) -> Optional[float]:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)],
            capture_output=True, timeout=30,
        )
        data = json.loads(out.stdout or "{}")
        return float(data.get("format", {}).get("duration", 0)) or None
    except Exception:
        return None


@router.post("/video/frames", summary="Extract key frames + OCR text from a YouTube video")
async def extract_video_frames(payload: FramesRequest):
    """Downloads a low-res sample, samples N frames, OCRs on-screen text.
    Degrades gracefully: reports which capabilities are missing instead of failing hard."""
    from app.engine.youtube_transcript import extract_video_id
    clean_id = extract_video_id(payload.url_or_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or ID")

    caps = {"yt_dlp": HAS_YTDLP, "ffmpeg": bool(shutil.which("ffmpeg")),
            "tesseract": HAS_TESSERACT, "pil": HAS_PIL}
    missing = [k for k, v in caps.items() if not v]

    if not HAS_YTDLP:
        return {"success": False, "video_id": clean_id, "capabilities": caps,
                "error": "yt-dlp not installed — run: pip install yt-dlp",
                "install_hint": "pip install yt-dlp  (+ ffmpeg + tesseract for OCR)"}

    work = Path(tempfile.mkdtemp(prefix="pr_frames_"))
    try:
        video_path = work / f"{clean_id}.mp4"
        ydl_opts = {
            "format": "worst[ext=mp4]/best[height<=360]/worst",
            "outtmpl": str(video_path),
            "quiet": True, "noprogress": True, "socket_timeout": 30,
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([f"https://www.youtube.com/watch?v={clean_id}"]))
        if not video_path.exists():
            return {"success": False, "video_id": clean_id, "capabilities": caps,
                    "error": "Download failed (video may be age-restricted or region-locked)"}

        duration = _probe_duration(video_path) or 0
        if duration <= 0:
            return {"success": False, "video_id": clean_id, "capabilities": caps,
                    "error": "ffprobe could not read duration — is ffmpeg installed?"}

        interval = payload.interval or max(1, int(duration / (payload.count + 1)))
        frames: List[Dict[str, Any]] = []
        for i in range(payload.count):
            t = min(max(interval * (i + 1), 0), max(duration - 1, 0))
            frame_path = work / f"frame_{i:02d}.jpg"
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(t), "-i", str(video_path),
                     "-frames:v", "1", "-q:v", "3", str(frame_path)],
                    capture_output=True, timeout=30,
                )
            except Exception as e:
                frames.append({"t": t, "error": f"ffmpeg failed: {e}"})
                continue
            if not frame_path.exists():
                frames.append({"t": t, "error": "frame extraction produced no file"})
                continue

            entry: Dict[str, Any] = {
                "t": round(t, 1),
                "timestamp": f"{int(t) // 60:02d}:{int(t) % 60:02d}",
                "permalink": f"https://www.youtube.com/watch?v={clean_id}&t={int(t)}s",
                "frame_b64": None, "ocr_text": None,
            }
            if HAS_PIL:
                try:
                    img = Image.open(frame_path)
                    img.thumbnail((480, 270))
                    import base64, io
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=68)
                    entry["frame_b64"] = base64.b64encode(buf.getvalue()).decode("ascii")
                except Exception:
                    pass
            if payload.ocr and HAS_TESSERACT:
                try:
                    txt = pytesseract.image_to_string(Image.open(frame_path)).strip()
                    entry["ocr_text"] = txt[:600] if txt else None
                except Exception:
                    pass
            frames.append(entry)

        ocr_count = sum(1 for f in frames if f.get("ocr_text"))
        return {"success": True, "video_id": clean_id, "duration": duration,
                "interval": interval, "capabilities": caps, "missing_for_full": missing,
                "frames": frames, "ocr_hits": ocr_count,
                "note": "Frames with OCR text often contain UI text, charts, pricing screens — high-signal evidence."}
    finally:
        shutil.rmtree(work, ignore_errors=True)


@router.get("/video/frames/status", summary="Frame extraction capability probe")
async def frames_status():
    return {
        "yt_dlp": HAS_YTDLP, "ffmpeg": bool(shutil.which("ffmpeg")),
        "tesseract": HAS_TESSERACT, "pil": HAS_PIL,
        "ready": HAS_YTDLP and bool(shutil.which("ffmpeg")),
        "ocr_ready": HAS_YTDLP and bool(shutil.which("ffmpeg")) and HAS_TESSERACT and HAS_PIL,
        "install": ["pip install yt-dlp pillow", "winget install Gyan.FFmpeg", "winget install UB-Mannheim.TesseractOCR"],
    }


# ===========================================================================
# Wave 2 — Tool Gateway (treg-inspired: ask for the task, not the tool)
# ===========================================================================

TOOL_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "serp_organic",
        "name": "Organic SERP",
        "category": "seo",
        "description": "Top organic results for a keyword via zero-auth SERP crawl.",
        "provider": "pulseradar-crawl",
        "internal": "serp",
        "params": [{"name": "keyword", "required": True, "type": "string", "description": "Keyword to search"}],
        "price_hint": "free",
        "enabled": True,
    },
    {
        "id": "youtube_search",
        "name": "YouTube Video Search",
        "category": "video",
        "description": "Search YouTube (delegates to the YouTube channel adapter + transcript engine).",
        "provider": "pulseradar-channel",
        "internal": "youtube",
        "params": [{"name": "keyword", "required": True, "type": "string", "description": "Search keyword"}],
        "price_hint": "free",
        "enabled": True,
    },
    {
        "id": "hackernews_search",
        "name": "Hacker News Search",
        "category": "developer",
        "description": "Algolia full-text search across HN posts and comments.",
        "provider": "algolia-hn",
        "internal": "hackernews",
        "params": [{"name": "keyword", "required": True, "type": "string", "description": "Search keyword"}],
        "price_hint": "free",
        "enabled": True,
    },
    {
        "id": "arxiv_search",
        "name": "arXiv Papers",
        "category": "research",
        "description": "Search arXiv preprints for technical/academic signal.",
        "provider": "arxiv-api",
        "internal": "arxiv",
        "params": [{"name": "keyword", "required": True, "type": "string", "description": "Search keyword"}],
        "price_hint": "free",
        "enabled": True,
    },
    {
        "id": "github_repos",
        "name": "GitHub Repo Search",
        "category": "developer",
        "description": "Search repositories (stars, activity, descriptions).",
        "provider": "github-api",
        "internal": "github",
        "params": [{"name": "keyword", "required": True, "type": "string", "description": "Search keyword"}],
        "price_hint": "free (60 req/h zero-auth)",
        "enabled": True,
    },
    {
        "id": "web_markdown",
        "name": "Page → Markdown",
        "category": "web",
        "description": "Fetch any URL as clean markdown (Firecrawl when keyed, reader fallback).",
        "provider": "firecrawl-or-reader",
        "internal": "web",
        "params": [{"name": "url", "required": True, "type": "string", "description": "Page URL"}],
        "price_hint": "free tier / fallback",
        "enabled": True,
    },
    {
        "id": "tweet_media_extract",
        "name": "Tweet Media & Poll Extract",
        "category": "social",
        "description": "FxEmbed extraction: photos, video links, poll results and true engagement for one status URL.",
        "provider": "fxembed",
        "internal": "tweet",
        "params": [{"name": "url", "required": True, "type": "string", "description": "x.com status URL"}],
        "price_hint": "free",
        "enabled": True,
    },
    {
        "id": "tweet_batch_extract",
        "name": "Tweet Batch Extract (session)",
        "category": "social",
        "description": "Scan a research session's raw feedback and enrich every tweet found with media/poll data.",
        "provider": "fxembed",
        "internal": "tweet_batch",
        "params": [{"name": "session_id", "required": True, "type": "string", "description": "Research session UUID"}],
        "price_hint": "free",
        "enabled": True,
    },
]

# ---------------------------------------------------------------------------
# social-media-scraping-apis catalog (3,268 scraped-API directory): we surface
# the PulseRadar-native equivalents that are live right now; external vendors
# from the directory can be enabled via the gateway config.
# ---------------------------------------------------------------------------
SCRAPING_API_DIRECTORY = {
    "source": "social-media-scraping-apis (community directory)",
    "total_apis": 3268,
    "live_integrations": [
        {"platform": "twitter/x", "status": "live", "engine": "FxEmbed + cookie-auth + DDG fallback"},
        {"platform": "youtube", "status": "live", "engine": "yt-dlp innerTube + browser cookies + Whisper"},
        {"platform": "reddit", "status": "live", "engine": "zero-auth JSON + live browser agent"},
        {"platform": "tiktok", "status": "planned", "engine": "directory vendor (see repo config)"},
        {"platform": "instagram", "status": "planned", "engine": "directory vendor (see repo config)"},
        {"platform": "facebook", "status": "live", "engine": "session cookies + crawler fallback"},
        {"platform": "linkedin", "status": "live", "engine": "authenticated profile session"},
    ],
}


@router.get("/gateway/tools", summary="Browse the tool catalog")
async def gateway_list_tools(category: Optional[str] = Query(None), q: Optional[str] = Query(None)):
    tools = TOOL_CATALOG
    if category:
        tools = [t for t in tools if t["category"] == category]
    if q:
        ql = q.lower()
        tools = [t for t in tools if ql in t["name"].lower() or ql in t["description"].lower()]
    return {"count": len(tools), "tools": tools,
            "directory": SCRAPING_API_DIRECTORY,
            "philosophy": "Ask for the task, not the tool — one request shape, many providers."}


@router.post("/gateway/call", summary="Invoke a catalog tool with a uniform request")
async def gateway_call(payload: GatewayCallRequest):
    tool = next((t for t in TOOL_CATALOG if t["id"] == payload.tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {payload.tool_id}")
    if not tool.get("enabled"):
        raise HTTPException(status_code=400, detail=f"Tool {payload.tool_id} is disabled")

    limit = payload.limit
    try:
        if tool["internal"] == "serp":
            keyword = str(payload.params.get("keyword") or "")
            if not keyword:
                raise HTTPException(status_code=400, detail="params.keyword is required")
            results = await _serp_search(keyword, limit)
            return {"tool": tool["id"], "success": True, "count": len(results), "results": results}

        if tool["internal"] in ("youtube", "hackernews", "arxiv", "github"):
            from app.channels import get_channel
            channel_map = {"youtube": "youtube", "hackernews": "hackernews", "arxiv": "arxiv", "github": "github"}
            ch = get_channel(channel_map[tool["internal"]])
            if not ch:
                raise HTTPException(status_code=503, detail="Channel unavailable")
            keyword = str(payload.params.get("keyword") or "")
            if not keyword:
                raise HTTPException(status_code=400, detail="params.keyword is required")
            items = await ch.search(keyword, limit=limit)
            return {
                "tool": tool["id"], "success": True, "count": len(items),
                "results": [{
                    "external_id": i.external_id, "channel": i.channel, "url": i.url,
                    "title": i.title, "content": (i.content or "")[:400],
                    "author": i.author, "engagement_score": i.engagement_score,
                } for i in items],
            }

        if tool["internal"] == "web":
            url = str(payload.params.get("url") or "")
            if not url.startswith(("http://", "https://")):
                raise HTTPException(status_code=400, detail="params.url must be http(s)")
            from app.engine.firecrawl_client import FirecrawlClient
            fc = FirecrawlClient()
            md = await fc.scrape_markdown(url) if hasattr(fc, "scrape_markdown") else None
            if not md:
                r = await _reader_fetch(url)
                md = r
            return {"tool": tool["id"], "success": bool(md), "markdown": (md or "")[:20000]}

        if tool["internal"] == "tweet":
            url = str(payload.params.get("url") or "")
            from app.engine.twitter_embeds import fetch_embed_data
            embeds = await fetch_embed_data(url)
            return {"tool": tool["id"], "success": bool(embeds), "results": [embeds] if embeds else []}

        if tool["internal"] == "tweet_batch":
            session_id = str(payload.params.get("session_id") or "")
            if not session_id:
                raise HTTPException(status_code=400, detail="params.session_id is required")
            from sqlalchemy import select
            from app.core.database import AsyncSessionLocal
            from app.models.entities import RawFeedback
            from app.engine.twitter_embeds import fetch_embed_data, TWEET_URL_REGEX
            import re as _re
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(RawFeedback).where(RawFeedback.session_id == session_id))
                rows = res.scalars().all()
            urls: List[str] = []
            for r in rows:
                for m in _re.finditer(TWEET_URL_REGEX, (r.url or "") + " " + (r.content or "")):
                    u = m.group(0)
                    if u not in urls:
                        urls.append(u)
            enriched = 0
            for u in urls[: payload.limit]:
                if await fetch_embed_data(u):
                    enriched += 1
            return {"tool": tool["id"], "success": True, "found": len(urls), "enriched": enriched}

        raise HTTPException(status_code=501, detail="Tool backend not implemented")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Gateway call {payload.tool_id} failed: {e}")
        return {"tool": payload.tool_id, "success": False, "error": str(e)}


async def _serp_search(keyword: str, limit: int) -> List[Dict[str, Any]]:
    """Zero-auth organic SERP via DuckDuckGo."""
    try:
        loop = asyncio.get_event_loop()
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        def _run():
            with DDGS() as d:
                return list(d.text(keyword, max_results=limit))
        rows = await loop.run_in_executor(None, _run)
        return [{"rank": i + 1, "title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
                for i, r in enumerate(rows)]
    except Exception as e:  # noqa: BLE001
        logger.warning(f"SERP fallback failed: {e}")
        return []


async def _reader_fetch(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": settings.REDDIT_USER_AGENT})
            if r.status_code != 200:
                return None
            text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", r.text)
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s{2,}", " ", text).strip()[:20000]
    except Exception:
        return None


# ===========================================================================
# Wave 3 — Clip Studio (AI-Shorts-Generator-inspired highlight ranking)
# ===========================================================================

HOOK_WORDS = ("secret", "mistake", "nobody", "truth", "biggest", "why", "how",
              "never", "always", "stop", "start", "lesson", "result", "framework",
              "problem", "actually", "insane", "crazy", "best", "worst", "shocking")
QUESTION_CUES = ("?", "what if", "imagine", "did you know")


def _viral_score(text: str, engagement_hint: float = 0.0) -> float:
    low = text.lower()
    words = low.split()
    if not words:
        return 0.0
    hook = sum(1 for w in HOOK_WORDS if w in low)
    question = 1 if any(c in low for c in QUESTION_CUES) else 0
    length_fit = 1.0 if 40 <= len(words) <= 130 else 0.55
    numbers = min(len(re.findall(r"\d+", low)) / 3, 1)
    return round(min(1.0, 0.30 * (hook / 3) + 0.15 * question + 0.25 * length_fit
                     + 0.10 * numbers + 0.20 * min(engagement_hint / 1000, 1.0)), 3)


@router.post("/clips/rank", summary="Rank viral clip segments from a video transcript")
async def rank_clips(payload: ClipRequest):
    """Sliding-window over transcript cues → scored candidate clips (no download needed)."""
    from app.engine.youtube_transcript import YouTubeTranscriptEngine, extract_video_id
    clean_id = extract_video_id(payload.url_or_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or ID")
    res = YouTubeTranscriptEngine.get_transcript(url_or_id=clean_id)
    snippets = res.get("snippets") or []
    if not snippets:
        raise HTTPException(status_code=400, detail="No timestamped transcript available for this video")

    candidates: List[Dict[str, Any]] = []
    win_start = 0
    for i in range(len(snippets)):
        # grow window from i
        j = i
        text_parts: List[str] = []
        start_t = float(snippets[i].get("start", 0))
        while j < len(snippets):
            end_t = float(snippets[j].get("start", 0)) + float(snippets[j].get("duration", 4))
            dur = end_t - start_t
            if dur > payload.max_duration:
                break
            text_parts.append(snippets[j].get("text", ""))
            j += 1
            if dur >= payload.min_duration:
                text = " ".join(text_parts).strip()
                score = _viral_score(text)
                candidates.append({
                    "start": round(start_t, 1), "end": round(end_t, 1),
                    "duration": round(dur, 1),
                    "start_ts": f"{int(start_t)//60:02d}:{int(start_t)%60:02d}",
                    "permalink": f"https://www.youtube.com/watch?v={clean_id}&t={int(start_t)}s",
                    "text": text[:800], "score": score,
                })
                if len(candidates) > 400:
                    break
        if len(candidates) > 400:
            break

    # Non-overlapping top-K selection
    candidates.sort(key=lambda c: c["score"], reverse=True)
    selected: List[Dict[str, Any]] = []
    for c in candidates:
        if all(c["end"] < s["start"] or c["start"] > s["end"] for s in selected):
            selected.append(c)
        if len(selected) >= payload.max_clips:
            break
    selected.sort(key=lambda c: c["start"])
    for rank, c in enumerate(selected, 1):
        c["rank"] = rank

    return {
        "success": True, "video_id": clean_id,
        "video_title": res.get("video_title"),
        "clips": selected,
        "candidates_evaluated": len(candidates),
        "algorithm": "sliding-window hook-word + question + pacing scorer (editable)",
    }


@router.post("/clips/cut", summary="Cut a clip segment to an mp4 file (requires ffmpeg)")
async def cut_clip(payload: ClipRequest):
    """Downloads low-res video and cuts [start,end] to an mp4."""
    if not (HAS_YTDLP and shutil.which("ffmpeg")):
        raise HTTPException(status_code=400, detail="yt-dlp + ffmpeg required for cutting")
    from app.engine.youtube_transcript import extract_video_id
    clean_id = extract_video_id(payload.url_or_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or ID")
    # Explicit start/end win; otherwise min/max durations are interpreted as bounds
    start = float(payload.start) if payload.start is not None else float(payload.min_duration)
    end = float(payload.end) if payload.end is not None else float(payload.max_duration)
    if end <= start:
        raise HTTPException(status_code=400, detail="end must exceed start")

    work = Path(tempfile.mkdtemp(prefix="pr_clip_"))
    try:
        video_path = work / f"{clean_id}.mp4"
        ydl_opts = {"format": "best[height<=720]/best", "outtmpl": str(video_path),
                    "quiet": True, "noprogress": True, "socket_timeout": 30}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([f"https://www.youtube.com/watch?v={clean_id}"]))
        if not video_path.exists():
            raise HTTPException(status_code=502, detail="Video download failed")
        out_name = f"clip_{clean_id}_{int(start)}s.mp4"
        out_path = EXPORT_DIR / out_name
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-ss", str(start), "-to", str(end),
            "-i", str(video_path), "-c", "copy", str(out_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0 or not out_path.exists():
            raise HTTPException(status_code=500, detail=f"ffmpeg cut failed: {stderr.decode()[:300]}")
        return {"success": True, "download_url": f"/api/v1/lab/clips/file/{out_name}",
                "file": out_name, "size_bytes": out_path.stat().st_size,
                "start": start, "end": end}
    finally:
        shutil.rmtree(work, ignore_errors=True)


@router.get("/clips/file/{name}", summary="Download a cut clip")
async def clip_file(name: str):
    from fastapi.responses import FileResponse
    safe = Path(name).name
    if not safe.endswith(".mp4") or "/" in safe or "\\" in safe:
        raise HTTPException(status_code=400, detail="Invalid file name")
    p = EXPORT_DIR / safe
    if not p.exists():
        raise HTTPException(status_code=404, detail="Clip not found (files are ephemeral)")
    return FileResponse(p, media_type="video/mp4", filename=safe)


# ===========================================================================
# Wave 3 — Security Posture Audit (shannon/security-audit-skill-inspired)
# ===========================================================================

SECURITY_CHECKS: List[Dict[str, Any]] = [
    {"id": "tls", "name": "HTTPS / TLS", "severity": "CRITICAL"},
    {"id": "hsts", "name": "Strict-Transport-Security", "severity": "HIGH"},
    {"id": "csp", "name": "Content-Security-Policy", "severity": "HIGH"},
    {"id": "xcto", "name": "X-Content-Type-Options", "severity": "MEDIUM"},
    {"id": "frame", "name": "X-Frame-Options / frame-ancestors", "severity": "MEDIUM"},
    {"id": "referrer", "name": "Referrer-Policy", "severity": "LOW"},
    {"id": "perms", "name": "Permissions-Policy", "severity": "LOW"},
    {"id": "cookies", "name": "Cookie Secure/SameSite flags", "severity": "HIGH"},
    {"id": "exposure", "name": "Sensitive file/dir exposure", "severity": "CRITICAL"},
    {"id": "server_banner", "name": "Server version disclosure", "severity": "LOW"},
]

SENSITIVE_PATHS = [".env", ".git/config", "backup.zip", "db.sqlite3", "composer.lock",
                   ".git/HEAD", "wp-config.php.bak", "debug.log", "dump.sql"]


@router.post("/security/audit", summary="Passive security posture audit (no exploits)")
async def security_audit(payload: SecurityAuditRequest):
    """Shannon-inspired but fully passive: header hygiene, cookie flags, exposure probes.
    Ethical boundary: GET-only probes on the target host, no exploitation."""
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.netloc
    if not host:
        raise HTTPException(status_code=400, detail="Invalid URL")

    findings: List[Dict[str, Any]] = []
    passed = 0
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": settings.REDDIT_USER_AGENT})
        except httpx.ConnectTimeout:
            raise HTTPException(status_code=504, detail="Target timed out")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Unreachable: {e}")

        headers = {k.lower(): v for k, v in resp.headers.items()}
        is_https = parsed.scheme == "https" or str(resp.url).startswith("https")

        def add(cid: str, status: str, detail: str):
            nonlocal passed
            findings.append({"check": cid, "status": status, "detail": detail})
            if status == "PASS":
                passed += 1

        add("tls", "PASS" if is_https else "FAIL", "HTTPS in use" if is_https else "Site served over plain HTTP")
        hsts = headers.get("strict-transport-security")
        add("hsts", "PASS" if hsts else "FAIL", hsts or "No HSTS header — downgrade attacks possible")
        csp = headers.get("content-security-policy")
        add("csp", "PASS" if csp else "PARTIAL", (csp[:120] + "…") if csp and len(csp) > 120 else (csp or "No CSP — XSS blast radius unbounded"))
        add("xcto", "PASS" if headers.get("x-content-type-options") else "FAIL", headers.get("x-content-type-options") or "MIME sniffing not blocked")
        frame = headers.get("x-frame-options") or ("frame-ancestors" in (csp or ""))
        add("frame", "PASS" if frame else "PARTIAL", "Clickjacking protection present" if frame else "No framing protection")
        add("referrer", "PASS" if headers.get("referrer-policy") else "PARTIAL", headers.get("referrer-policy") or "No referrer policy")
        add("perms", "PASS" if headers.get("permissions-policy") else "PARTIAL", headers.get("permissions-policy") or "No permissions policy")
        cookies = resp.headers.get("set-cookie", "")
        if cookies:
            secure_ok = "secure" in cookies.lower() and "samesite" in cookies.lower()
            add("cookies", "PASS" if secure_ok else "FAIL",
                "Secure+SameSite flags set" if secure_ok else "Cookies missing Secure/SameSite flags")
        else:
            add("cookies", "PASS", "No cookies set on this response")

        server_banner = headers.get("server", "")
        disclosive = bool(re.search(r"\d+\.\d+", server_banner))
        add("server_banner", "PASS" if not disclosive else "PARTIAL",
            "Version hidden" if not disclosive else f"Version disclosed: {server_banner}")

        # Exposure probes (GET only, limited count)
        exposed = []
        for p in SENSITIVE_PATHS:
            try:
                pr = await client.get(f"{parsed.scheme}://{host}/{p}", headers={"User-Agent": settings.REDDIT_USER_AGENT})
                if pr.status_code == 200 and len(pr.content) > 0:
                    ct = pr.headers.get("content-type", "")
                    if "text/html" not in ct or p.endswith((".zip", ".sql", ".log")):
                        exposed.append(f"/{p}")
            except Exception:
                continue
            if len(exposed) >= 3:
                break
        add("exposure", "FAIL" if exposed else "PASS",
            f"Exposed: {', '.join(exposed)}" if exposed else "No sensitive files exposed")

    total = len(findings)
    score = round(100 * passed / total)
    severity_fail = [f for f in findings if f["status"] == "FAIL"]
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return {
        "success": True, "url": str(resp.url), "host": host,
        "score": score, "grade": grade,
        "passed": passed, "total": total,
        "status_counts": {
            "PASS": sum(1 for f in findings if f["status"] == "PASS"),
            "PARTIAL": sum(1 for f in findings if f["status"] == "PARTIAL"),
            "FAIL": sum(1 for f in findings if f["status"] == "FAIL"),
        },
        "critical_failures": [f for f in severity_fail
                              if next(c for c in SECURITY_CHECKS if c["id"] == f["check"])["severity"] == "CRITICAL"],
        "findings": findings,
        "checklist": SECURITY_CHECKS,
        "boundary": "Passive audit: header analysis + GET exposure probes only. No exploitation (Shannon OSS goes further with authorized pentests).",
    }


# ===========================================================================
# Wave 3 — Traffic Correlation (laravel-analytics-inspired GA4 patterns)
# ===========================================================================

@router.post("/seo/traffic-correlation", summary="Correlate SEO audit score with GA4-style traffic data")
async def traffic_correlation(payload: Ga4CorrelationRequest):
    """Correlates stored SEO audit scores for a domain with GA4 traffic (when
    GOOGLE_API_KEY + GA4 property are configured; otherwise simulates the
    correlation table so the feature is demonstrable end-to-end)."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.seo_entities import SeoAuditSession

    domain = payload.domain.strip().lower().replace("https://", "").replace("http://", "").strip("/")
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(SeoAuditSession)
            .where(SeoAuditSession.domain.contains(domain))
            .order_by(SeoAuditSession.created_at.desc())
            .limit(12)
        )
        audits = res.scalars().all()

    audit_points = [{"audit_id": a.id, "date": a.created_at.isoformat(),
                     "overall_score": a.overall_score, "url": a.url} for a in audits]

    ga4_ready = bool(settings.GOOGLE_API_KEY)
    traffic_series: List[Dict[str, Any]] = []
    correlation: Optional[float] = None
    note = ""

    if ga4_ready and payload.audit_id:
        note = "Live GA4 fetch requires service-account credentials wired to your property (see laravel-analytics patterns)."
        # Live GA4 Data API integration point — runReport on sessions/pageviews.
    else:
        # Deterministic demonstration series anchored to audit dates
        import hashlib
        base = 800 + int(hashlib.md5(domain.encode()).hexdigest(), 16) % 1500
        for i, a in enumerate(reversed(audit_points)):
            drift = (a["overall_score"] - 60) * 22
            traffic_series.append({"date": a["date"], "sessions": max(0, base + drift + i * 35),
                                   "pageviews": max(0, int((base + drift + i * 35) * 1.6))})
        if len(traffic_series) >= 2 and all("overall_score" in p for p in audit_points):
            correlation = _pearson([p["overall_score"] for p in audit_points],
                                   [t["sessions"] for t in traffic_series])
        note = "Demonstration series (no GA4 credentials). Add GOOGLE_API_KEY + GA4 property for live data."

    return {
        "success": True, "domain": domain,
        "audits": audit_points, "traffic_series": traffic_series,
        "correlation": correlation,
        "interpretation": _corr_text(correlation),
        "ga4_ready": ga4_ready, "note": note,
    }


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = min(len(xs), len(ys))
    if n < 2:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) ** 0.5) * (sum((y - my) ** 2 for y in ys) ** 0.5)
    return round(num / den, 3) if den else None


def _corr_text(r: Optional[float]) -> str:
    if r is None:
        return "Not enough audit history for correlation."
    a = abs(r)
    strength = "strong" if a >= 0.7 else "moderate" if a >= 0.4 else "weak"
    direction = "positive" if r > 0 else "negative"
    return f"{strength.capitalize()} {direction} correlation (r={r}) between audit score and sessions."


# ===========================================================================
# Wave 4 — Workflow Orchestrator (Dagu-inspired DAGs)
# ===========================================================================

WORKFLOWS_PATH = BACKEND_DIR / "data" / "workflows.json"
_workflow_lock = asyncio.Lock()


def _load_workflows() -> List[Dict[str, Any]]:
    if WORKFLOWS_PATH.exists():
        try:
            return json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_workflows(items: List[Dict[str, Any]]) -> None:
    WORKFLOWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = WORKFLOWS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    tmp.replace(WORKFLOWS_PATH)


@router.get("/workflows", summary="List workflows with run history")
async def workflows_list():
    items = _load_workflows()
    return {"count": len(items), "workflows": items}


@router.post("/workflows", summary="Create a workflow DAG")
async def workflows_create(payload: WorkflowCreateRequest):
    # Validate DAG: detect cycles via DFS
    step_map = {s.name: s for s in payload.steps}
    if len(step_map) != len(payload.steps):
        raise HTTPException(status_code=400, detail="Duplicate step names")
    visiting, visited = set(), set()

    def dfs(n: str) -> bool:
        if n in visiting:
            return True
        if n in visited:
            return False
        visiting.add(n)
        for dep in step_map[n].depends_on:
            if dep not in step_map:
                raise HTTPException(status_code=400, detail=f"Step '{n}' depends on unknown step '{dep}'")
            if dfs(dep):
                return True
        visiting.remove(n)
        visited.add(n)
        return False

    for name in step_map:
        if dfs(name):
            raise HTTPException(status_code=400, detail=f"Cycle detected at step '{name}'")

    wf = {
        "id": str(uuid.uuid4()), "name": payload.name, "description": payload.description,
        "steps": [s.model_dump() for s in payload.steps],
        "schedule": payload.schedule, "interval_hours": payload.interval_hours,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "runs": [], "enabled": True,
    }
    async with _workflow_lock:
        items = _load_workflows()
        items.insert(0, wf)
        _save_workflows(items)
    return {"success": True, "workflow": wf}


@router.delete("/workflows/{wf_id}", summary="Delete a workflow")
async def workflows_delete(wf_id: str):
    async with _workflow_lock:
        items = _load_workflows()
        remaining = [w for w in items if w["id"] != wf_id]
        if len(remaining) == len(items):
            raise HTTPException(status_code=404, detail="Workflow not found")
        _save_workflows(remaining)
    return {"success": True}


@router.post("/workflows/{wf_id}/run", summary="Execute a workflow DAG (topological order)")
async def workflows_run(wf_id: str, body: WorkflowRunBody):
    async with _workflow_lock:
        items = _load_workflows()
        wf = next((w for w in items if w["id"] == wf_id), None)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    run_id = str(uuid.uuid4())
    started = datetime.utcnow().isoformat() + "Z"
    logs: List[Dict[str, Any]] = []

    # Topological order (Kahn)
    steps = {s["name"]: s for s in wf["steps"]}
    indeg = {n: 0 for n in steps}
    dependents: Dict[str, List[str]] = {n: [] for n in steps}
    for n, s in steps.items():
        for dep in s.get("depends_on", []):
            if dep in steps:
                indeg[n] += 1
                dependents[dep].append(n)
    queue = sorted([n for n, d in indeg.items() if d == 0])
    order: List[str] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in dependents[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    if len(order) != len(steps):
        raise HTTPException(status_code=400, detail="Workflow contains a cycle")

    for n in order:
        s = steps[n]
        entry = {"step": n, "type": s["type"], "status": "RUNNING", "started": datetime.utcnow().isoformat() + "Z"}
        logs.append(entry)
        try:
            result = await _execute_step(s)
            entry["status"] = "OK" if result.get("success", True) else "WARN"
            entry["result"] = result
        except Exception as e:  # noqa: BLE001
            entry["status"] = "FAIL"
            entry["error"] = str(e)
        entry["finished"] = datetime.utcnow().isoformat() + "Z"

    ok = all(l["status"] in ("OK", "WARN") for l in logs)
    run_record = {"run_id": run_id, "trigger": body.trigger, "started": started,
                  "finished": datetime.utcnow().isoformat() + "Z", "status": "OK" if ok else "PARTIAL/FAIL"}
    async with _workflow_lock:
        items = _load_workflows()
        wf = next((w for w in items if w["id"] == wf_id), None)
        if wf:
            wf.setdefault("runs", []).append({"id": run_id, "started": started,
                                              "status": run_record["status"],
                                              "steps": [{"step": l["step"], "status": l["status"]} for l in logs]})
            wf["runs"] = wf["runs"][-20:]
            _save_workflows(items)
    return {"success": ok, "run": run_record, "logs": logs}


async def _execute_step(step: Dict[str, Any]) -> Dict[str, Any]:
    stype, cfg = step["type"], step.get("config", {})
    if stype == "research.run":
        from app.channels import get_channel
        query = cfg.get("query") or ""
        channels = cfg.get("channels") or ["reddit", "hackernews"]
        total = 0
        for cname in channels[:6]:
            ch = get_channel(cname)
            if not ch:
                continue
            try:
                items = await asyncio.wait_for(ch.search(query, limit=int(cfg.get("limit", 15))), timeout=25)
                total += len(items)
            except Exception:
                continue
        return {"success": total > 0, "query": query, "items": total}
    if stype == "seo.audit":
        url = cfg.get("url") or ""
        if not url:
            return {"success": False, "error": "config.url required"}
        from app.seo.engine import SeoAuditEngine
        engine = SeoAuditEngine()
        result = await engine.run_audit(url=url, audit_type=cfg.get("audit_type", "quick"))
        return {"success": bool(result.get("success")), "scores": result.get("scores", {})}
    if stype == "lab.backup":
        from app.engine.backup_manager import create_backup
        manifest = create_backup(cfg.get("name", "workflow"), note=f"workflow:{step['name']}")
        return {"success": True, "snapshot_id": manifest["snapshot_id"]}
    if stype == "webhook":
        url = cfg.get("url") or ""
        if not url.startswith("http"):
            return {"success": False, "error": "config.url required"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=cfg.get("payload", {"event": "workflow.step"}))
            return {"success": r.status_code < 400, "status_code": r.status_code}
    return {"success": False, "error": f"Unknown step type: {stype}"}


# ===========================================================================
# Wave 4 — Signals Mega-Grid (glide-data-grid-inspired feed)
# ===========================================================================

@router.get("/grid/signals", summary="Flat, paginated signal feed across ALL sessions for a virtualized grid")
async def grid_signals(
    q: Optional[str] = Query(None, description="Substring filter on title/content"),
    channel: Optional[str] = Query(None),
    sort: str = Query("engagement", description="engagement | recent"),
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
):
    from sqlalchemy import select, desc
    from app.core.database import AsyncSessionLocal
    from app.models.entities import RawFeedback

    async with AsyncSessionLocal() as db:
        stmt = select(RawFeedback)
        if channel:
            stmt = stmt.where(RawFeedback.channel == channel)
        if q:
            stmt = stmt.where(RawFeedback.content.contains(q))
        if sort == "recent":
            stmt = stmt.order_by(desc(RawFeedback.created_at))
        else:
            stmt = stmt.order_by(desc(RawFeedback.engagement_score))
        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        rows = res.scalars().all()

        items = [{
            "id": r.id, "channel": r.channel, "title": r.title or (r.content or "")[:80],
            "author": r.author, "engagement": r.engagement_score,
            "url": r.url, "created_at": r.created_at.isoformat(),
            "preview": (r.content or "")[:160],
            "has_transcript": bool((r.raw_metadata or {}).get("has_transcript")),
        } for r in rows]
        return {"count": len(items), "offset": offset, "limit": limit, "items": items}


@router.get("/grid/channels", summary="Channel facets for grid filters")
async def grid_channels():
    from sqlalchemy import func, select
    from app.core.database import AsyncSessionLocal
    from app.models.entities import RawFeedback
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(RawFeedback.channel, func.count()).group_by(RawFeedback.channel))
        rows = res.all()
    return {"channels": [{"channel": c, "count": n} for c, n in rows]}


# ===========================================================================
# Wave 4 — Browser Authenticated Session (BrowserSkill-inspired config)
# ===========================================================================

@router.get("/browser/session", summary="Inspect authenticated browser-session config")
async def browser_session_get():
    env_dir = (getattr(settings, "BROWSER_USER_DATA_DIR", "") or "").strip()
    profile_valid = bool(env_dir) and Path(env_dir).isdir() if env_dir else False
    return {
        "user_data_dir": env_dir,
        "configured": bool(env_dir),
        "profile_valid": profile_valid,
        "how_to": [
            "Close Chrome completely (it locks the profile dir).",
            "Set BROWSER_USER_DATA_DIR in .env to your Chrome user-data dir, e.g.",
            "  Windows: C:\\Users\\<you>\\AppData\\Local\\Google\\Chrome\\User Data",
            "Restart the backend — LiveBrowserAgent then reuses your logged-in sessions.",
        ],
        "benefit": "Walled-garden channels (X, LinkedIn, Facebook) run with your real session cookies — no headless login flows.",
        "channels_benefiting": ["twitter", "linkedin", "facebook"],
        "safety": "Profile is used read-only for scraping; no clicks, no form submissions.",
    }


@router.post("/browser/session", summary="Set authenticated browser-session dir (runtime)")
async def browser_session_set(payload: BrowserSessionConfigBody):
    if payload.user_data_dir is not None:
        settings.BROWSER_USER_DATA_DIR = payload.user_data_dir.strip()
    return {"success": True, "user_data_dir": getattr(settings, "BROWSER_USER_DATA_DIR", ""),
            "note": "Runtime-only; persist by adding BROWSER_USER_DATA_DIR to .env"}
