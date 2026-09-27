"""YouTube Transcript & Video Intelligence API Endpoints (PulseRadar)
On-demand transcript retrieval, subtitle extraction, Whisper ASR fallback, and in-site video playback data.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.engine.youtube_transcript import YouTubeTranscriptEngine, extract_video_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube Transcripts & Video Intelligence"])


class TranscriptRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL (watch, youtu.be, shorts) or 11-char Video ID")
    languages: Optional[List[str]] = Field(default=["en", "en-US", "en-GB"], description="Language priority list")
    force_whisper: Optional[bool] = Field(default=False, description="Force Whisper audio transcription")
    whisper_key: Optional[str] = Field(default=None, description="Optional custom Groq or OpenAI Whisper key")


class TranscribeAudioRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL or 11-char Video ID")
    api_key: Optional[str] = Field(default=None, description="Groq API key or OpenAI key")
    provider: Optional[str] = Field(default="auto", description="Provider: 'groq' (free), 'openai', or 'auto'")


class TranscriptSnippet(BaseModel):
    text: str
    start: float
    duration: float
    timestamp: str
    permalink: str


class TranscriptStats(BaseModel):
    duration_seconds: float
    formatted_duration: Optional[str] = "00:00"
    snippets_count: int
    word_count: int


class TranscriptResponse(BaseModel):
    success: bool
    video_id: str
    video_url: str
    video_title: Optional[str] = None
    channel: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    has_transcript: Optional[bool] = True
    is_transcribed: Optional[bool] = False
    is_chapters_only: Optional[bool] = False
    source: Optional[str] = "youtube_subtitles"
    language: Optional[str] = "en"
    is_generated: Optional[bool] = False
    text: str
    timestamped_text: Optional[str] = ""
    snippets: List[TranscriptSnippet] = []
    stats: TranscriptStats
    whisper_available: Optional[bool] = False
    notice: Optional[str] = None
    error: Optional[str] = None


@router.post("/transcript", response_model=TranscriptResponse)
async def get_video_transcript(payload: TranscriptRequest):
    """Fetches the subtitle transcript or navigational cues for any YouTube video.
    Guarantees a clean, structured response without raw unhandled 404 crashes.
    """
    langs = tuple(payload.languages) if payload.languages else ("en", "en-US", "en-GB")
    res = YouTubeTranscriptEngine.get_transcript(
        url_or_id=payload.url_or_id,
        languages=langs,
        force_whisper=payload.force_whisper or False,
        whisper_key=payload.whisper_key
    )
    if not res.get("success") and not res.get("video_id"):
        raise HTTPException(
            status_code=400,
            detail=res.get("error", "Invalid YouTube URL or ID.")
        )
    return res


@router.get("/transcript/{video_id}", response_model=TranscriptResponse)
async def get_video_transcript_by_id(
    video_id: str,
    languages: Optional[str] = Query("en,en-US,en-GB", description="Comma-separated language codes"),
    force_whisper: Optional[bool] = Query(False, description="Force Whisper audio transcription")
):
    """GET endpoint to fetch video transcript by ID or permalink query."""
    lang_list = tuple(l.strip() for l in languages.split(",") if l.strip()) if languages else ("en", "en-US")
    res = YouTubeTranscriptEngine.get_transcript(
        url_or_id=video_id,
        languages=lang_list,
        force_whisper=force_whisper
    )
    if not res.get("success") and not res.get("video_id"):
        raise HTTPException(
            status_code=400,
            detail=res.get("error", "Invalid YouTube video ID.")
        )
    return res


@router.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_video_audio(payload: TranscribeAudioRequest):
    """Downloads YouTube audio and transcribes dialogue using Groq Whisper large v3 or OpenAI Whisper."""
    res = YouTubeTranscriptEngine.transcribe_audio_with_whisper(
        video_id_or_url=payload.url_or_id,
        api_key=payload.api_key,
        provider=payload.provider or "auto"
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=400,
            detail=res.get("error", "Failed to transcribe audio.")
        )
    return res


@router.get("/info/{video_id}")
async def get_video_metadata(video_id: str):
    """Extracts fast video metadata (title, duration, channel, chapters, thumbnail) without downloading."""
    clean_id = extract_video_id(video_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")
    return YouTubeTranscriptEngine.get_video_info(clean_id)


from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
import shutil
from app.engine.youtube_downloader import YouTubeDownloadEngine
from app.engine.youtube_transcript import resolve_transcription_keys


class DownloadMediaRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL or 11-char Video ID")
    type: str = Field(default="video", description="'video', 'audio', or 'subtitle'")
    quality: Optional[str] = Field(default="720", description="Target video resolution, e.g. '1080', '720', '480', '360'")
    audio_format: Optional[str] = Field(default="mp3", description="'mp3', 'm4a', 'wav', 'flac'")
    audio_bitrate: Optional[str] = Field(default="192", description="'320', '192', '128', 'best'")
    format_id: Optional[str] = Field(default=None, description="Exact yt-dlp format ID")
    sub_lang: Optional[str] = Field(default="en", description="Subtitle language code, e.g. 'en'")
    sub_format: Optional[str] = Field(default="srt", description="'srt' or 'vtt'")
    audio_normalization: Optional[bool] = Field(default=False, description="Apply EBU R128 audio normalization")


def _cleanup_temp_dir(file_path: str):
    """Safely cleans up temporary file and its enclosing directory after streaming."""
    try:
        if os.path.exists(file_path):
            parent_dir = os.path.dirname(file_path)
            if "pulseradar_dl_" in parent_dir and os.path.exists(parent_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)
            else:
                os.remove(file_path)
    except Exception as e:
        logger.debug(f"Error removing temp download file {file_path}: {e}")


@router.get("/whisper-status")
async def get_whisper_status():
    """Checks if Gemini Flash Multimodal, Groq Whisper, or OpenAI Whisper is configured."""
    keys = resolve_transcription_keys()
    gemini_configured = bool(keys.get("google"))
    groq_configured = bool(keys.get("groq"))
    openai_configured = bool(keys.get("openai"))
    is_ready = gemini_configured or groq_configured or openai_configured

    default_provider = "gemini" if gemini_configured else ("groq" if groq_configured else ("openai" if openai_configured else "none"))

    return {
        "gemini_configured": gemini_configured,
        "groq_configured": groq_configured,
        "openai_configured": openai_configured,
        "whisper_ready": is_ready,
        "default_provider": default_provider,
        "model": "gemini-3.5-flash-lite" if default_provider == "gemini" else getattr(settings, "WHISPER_MODEL", "whisper-large-v3")
    }


@router.get("/formats")
async def get_formats_get(url: str = Query(..., description="YouTube URL or 11-char Video ID")):
    """Extracts all downloadable video formats, audio presets, and subtitle tracks (YTSage engine)."""
    res = YouTubeDownloadEngine.get_available_formats(url)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to extract formats."))
    return res


@router.post("/formats")
async def get_formats_post(payload: TranscriptRequest):
    """Extracts all downloadable video formats, audio presets, and subtitle tracks via POST."""
    res = YouTubeDownloadEngine.get_available_formats(payload.url_or_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to extract formats."))
    return res


@router.get("/download")
async def download_media_get(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="YouTube URL or video ID"),
    type: str = Query("video", description="'video', 'audio', or 'subtitle'"),
    quality: str = Query("720", description="Video quality (1080, 720, 480, 360)"),
    audio_format: str = Query("mp3", description="Audio format (mp3, m4a, wav, flac)"),
    audio_bitrate: str = Query("192", description="Audio bitrate (320, 192, 128)"),
    format_id: Optional[str] = Query(None, description="Exact yt-dlp format ID"),
    sub_lang: str = Query("en", description="Subtitle language code"),
    sub_format: str = Query("srt", description="Subtitle format ('srt' or 'vtt')"),
    normalize: bool = Query(False, description="Enable audio normalization")
):
    """Downloads requested YouTube media and streams directly to user with attachment headers."""
    try:
        file_path, filename, mime_type = YouTubeDownloadEngine.execute_media_download(
            url_or_id=url,
            media_type=type,
            quality=quality,
            audio_format=audio_format,
            audio_bitrate=audio_bitrate,
            format_id=format_id,
            subtitle_lang=sub_lang,
            subtitle_format=sub_format,
            audio_normalization=normalize,
        )

        background_tasks.add_task(_cleanup_temp_dir, file_path)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    except Exception as e:
        logger.error(f"Download execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_media_post(
    payload: DownloadMediaRequest,
    background_tasks: BackgroundTasks
):
    """Downloads requested YouTube media via POST and streams directly as file attachment."""
    try:
        file_path, filename, mime_type = YouTubeDownloadEngine.execute_media_download(
            url_or_id=payload.url_or_id,
            media_type=payload.type,
            quality=payload.quality or "720",
            audio_format=payload.audio_format or "mp3",
            audio_bitrate=payload.audio_bitrate or "192",
            format_id=payload.format_id,
            subtitle_lang=payload.sub_lang or "en",
            subtitle_format=payload.sub_format or "srt",
            audio_normalization=payload.audio_normalization or False,
        )

        background_tasks.add_task(_cleanup_temp_dir, file_path)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    except Exception as e:
        logger.error(f"Download execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals")
async def extract_transcript_signals(payload: TranscriptRequest):
    """Fetches transcript and chunks it into verbatim signal items with exact YouTube second permalinks."""
    langs = tuple(payload.languages) if payload.languages else ("en", "en-US", "en-GB")
    res = YouTubeTranscriptEngine.get_transcript(payload.url_or_id, languages=langs)
    if not res.get("success") and not res.get("video_id"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to retrieve transcript"))
    
    chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(res, min_words_per_chunk=35, max_words_per_chunk=75)
    return {
        "video_id": res["video_id"],
        "video_url": res["video_url"],
        "video_title": res.get("video_title"),
        "total_chunks": len(chunks),
        "stats": res["stats"],
        "signals": chunks
    }
