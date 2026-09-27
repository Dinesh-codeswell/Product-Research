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


@router.get("/whisper-status")
async def get_whisper_status():
    """Checks if Groq or OpenAI Whisper ASR is configured in backend settings."""
    groq_configured = bool(getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", ""))
    openai_configured = bool(getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""))
    return {
        "groq_configured": groq_configured,
        "openai_configured": openai_configured,
        "whisper_ready": groq_configured or openai_configured,
        "default_provider": "groq" if groq_configured else ("openai" if openai_configured else "none"),
        "model": getattr(settings, "WHISPER_MODEL", "whisper-large-v3")
    }


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
