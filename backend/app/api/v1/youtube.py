"""YouTube Transcript API Endpoints (PulseRadar)
On-demand transcript retrieval, subtitle extraction, and AI signal chunking.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.engine.youtube_transcript import YouTubeTranscriptEngine, extract_video_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube Transcripts"])


class TranscriptRequest(BaseModel):
    url_or_id: str = Field(..., description="YouTube URL (watch, youtu.be, shorts) or 11-char Video ID")
    languages: Optional[List[str]] = Field(default=["en", "en-US", "en-GB"], description="Language priority list")


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
    language: Optional[str] = "en"
    is_generated: Optional[bool] = False
    text: str
    timestamped_text: Optional[str] = ""
    snippets: List[TranscriptSnippet] = []
    stats: TranscriptStats
    error: Optional[str] = None


@router.post("/transcript", response_model=TranscriptResponse)
async def get_video_transcript(payload: TranscriptRequest):
    """Fetches the subtitle transcript and cues for any YouTube video without API keys or headless browsers."""
    langs = tuple(payload.languages) if payload.languages else ("en", "en-US", "en-GB")
    res = YouTubeTranscriptEngine.get_transcript(payload.url_or_id, languages=langs)
    if not res.get("success"):
        raise HTTPException(
            status_code=404 if "No transcript" in res.get("error", "") else 400,
            detail=res.get("error", "Failed to retrieve transcript")
        )
    return res


@router.get("/transcript/{video_id}", response_model=TranscriptResponse)
async def get_video_transcript_by_id(
    video_id: str,
    languages: Optional[str] = Query("en,en-US,en-GB", description="Comma-separated language codes")
):
    """GET endpoint to fetch video transcript by ID or permalink query."""
    lang_list = tuple(l.strip() for l in languages.split(",") if l.strip()) if languages else ("en", "en-US")
    res = YouTubeTranscriptEngine.get_transcript(video_id, languages=lang_list)
    if not res.get("success"):
        raise HTTPException(
            status_code=404 if "No transcript" in res.get("error", "") else 400,
            detail=res.get("error", "Failed to retrieve transcript")
        )
    return res


@router.post("/signals")
async def extract_transcript_signals(payload: TranscriptRequest):
    """Fetches transcript and chunks it into verbatim signal items with exact YouTube second permalinks."""
    langs = tuple(payload.languages) if payload.languages else ("en", "en-US", "en-GB")
    res = YouTubeTranscriptEngine.get_transcript(payload.url_or_id, languages=langs)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Failed to retrieve transcript"))
    
    chunks = YouTubeTranscriptEngine.chunk_transcript_into_signals(res, min_words_per_chunk=35, max_words_per_chunk=75)
    return {
        "video_id": res["video_id"],
        "video_url": res["video_url"],
        "total_chunks": len(chunks),
        "stats": res["stats"],
        "signals": chunks
    }
